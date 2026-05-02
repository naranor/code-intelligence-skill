import sys
import os
import ast
import argparse
import subprocess
import json
import time
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Internal language database
LANG_DATA = {
    "python": {"id": "python", "lsp": None},
    "java":   {"id": "java",   "lsp": "jdtls"},
    "go":     {"id": "go",     "lsp": "gopls"},
    "rust":   {"id": "rust",   "lsp": "rust-analyzer"},
}

ALIASES = {
    "py": "python", "python": "python", ".py": "python",
    "java": "java", ".java": "java",
    "go": "go", "golang": "go", ".go": "go",
    "rs": "rust", "rust": "rust", ".rs": "rust"
}

class MinimalLspClient:
    """
    Standalone JSON-RPC client for Language Servers.
    Features a background thread to prevent pipe deadlocks during heavy indexing.
    """
    def __init__(self, command: List[str], root_path: Path, lang_id: str):
        self.command = command
        self.root_path = root_path
        self.lang_id = lang_id
        self.process = None
        self.msg_id = 1
        self._responses = []
        self._reader_thread = None

    def start(self):
        if self.process and self.process.poll() is None: return
        
        print(f"[LSP] Starting '{self.command[0]}' for {self.lang_id}...")
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )

        def reader():
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline().decode("utf-8")
                    if line.startswith("Content-Length:"):
                        length = int(line.split(":")[1].strip())
                        self.process.stdout.readline()
                        data = self.process.stdout.read(length).decode("utf-8")
                        self._responses.append(json.loads(data))
                except: break
        
        self._reader_thread = threading.Thread(target=reader, daemon=True)
        self._reader_thread.start()

    def _send(self, method: str, params: dict):
        req = {"jsonrpc": "2.0", "id": self.msg_id, "method": method, "params": params}
        content = json.dumps(req)
        self.process.stdin.write(f"Content-Length: {len(content)}\r\n\r\n{content}".encode("utf-8"))
        self.process.stdin.flush()
        self.msg_id += 1

    def _receive(self, timeout: int = 30) -> Optional[dict]:
        start = time.time()
        while time.time() - start < timeout:
            if self._responses: return self._responses.pop(0)
            time.sleep(0.1)
        return None

    def initialize(self):
        self.start()
        self._send("initialize", {
            "processId": os.getpid(),
            "rootUri": self.root_path.as_uri(),
            "capabilities": {"workspace": {"applyEdit": True}}
        })
        for _ in range(50):
            res = self._receive(timeout=2)
            if res and "id" in res: break
        self._send("initialized", {})

    def rename(self, file_path: Path, line: int, col: int, new_name: str) -> Optional[dict]:
        self.initialize()
        self._send("textDocument/rename", {
            "textDocument": {"uri": file_path.as_uri()},
            "position": {"line": line, "character": col},
            "newName": new_name
        })
        for _ in range(100):
            res = self._receive(timeout=2)
            if res and "id" in res and res.get("id") == (self.msg_id - 1):
                return res.get("result")
        return None

class UltimateSafeEditor:
    def __init__(self):
        self._lsp_clients: Dict[str, MinimalLspClient] = {}

    def _get_lsp_client(self, lang_id: str, root_path: Path) -> Optional[MinimalLspClient]:
        if lang_id not in self._lsp_clients:
            info = LANG_DATA.get(lang_id)
            if not info or not info["lsp"]: return None
            
            lsp_bin = info["lsp"]
            possible = [lsp_bin, os.path.expanduser(f"~/go/bin/{lsp_bin}"), os.path.expanduser(f"~/.local/bin/{lsp_bin}")]
            found = None
            for p in possible:
                try:
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        found = p
                        break
                except: continue
            if not found: return None
            self._lsp_clients[lang_id] = MinimalLspClient([found], root_path, lang_id)
            
        return self._lsp_clients[lang_id]

    def verify_syntax(self, code: str, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            try: ast.parse(code); return True
            except SyntaxError as e: print(f"❌ Python Error: {e}"); return False
        try:
            from tree_sitter import Language, Parser
            lang_id = ALIASES.get(ext)
            mod = __import__(f"tree_sitter_{lang_id}")
            parser = Parser(Language(mod.language()))
            return not parser.parse(bytes(code, "utf8")).root_node.has_error
        except: return True

    def smart_replace(self, file_path: str, old: str, new: str) -> str:
        fp = Path(file_path).resolve()
        content = fp.read_text(encoding="utf-8")
        if content.count(old) != 1: return f"Error: Match not unique ({content.count(old)} found)."
        new_content = content.replace(old, new)
        if not self.verify_syntax(new_content, file_path): return "Aborting: Syntax error."
        fp.write_text(new_content, encoding="utf-8")
        return f"Successfully updated {file_path}."

    def rename_symbol(self, file_path: str, symbol: str, new_name: str, root_path: str = ".") -> str:
        abs_file = Path(file_path).resolve()
        abs_root = Path(root_path).resolve()
        lang_id = ALIASES.get(abs_file.suffix.lower())
        
        if lang_id == "python":
            try:
                from rope.base.project import Project
                from rope.refactor.rename import Rename
                project = Project(str(abs_root))
                res = project.get_resource(str(abs_file.relative_to(abs_root)))
                project.do(Rename(project, res, res.read().find(symbol)).get_changes(new_name))
                project.close(); return f"Renamed '{symbol}' to '{new_name}' (Python/Rope)."
            except Exception as e: return f"Rename failed: {e}"

        client = self._get_lsp_client(lang_id, abs_root)
        if not client: return f"Error: LSP not found for {lang_id}."

        content = abs_file.read_text()
        lines = content.splitlines()
        pos = next(((i, line.find(symbol)) for i, line in enumerate(lines) if line.find(symbol) != -1), None)
        if not pos: return "Error: Symbol not found."
        
        if lang_id == "go":
            res = subprocess.run([client.command[0], "rename", "-w", f"{abs_file}:{pos[0]+1}:{pos[1]+1}", new_name], capture_output=True, text=True)
            return "Rename successful." if res.returncode == 0 else f"Gopls Error: {res.stderr}"

        edit = client.rename(abs_file, pos[0], pos[1], new_name)
        if not edit: return "LSP Error: No edits received."
        
        for uri, file_edits in edit.get("changes", {}).items():
            p = Path(uri.replace("file://", ""))
            f_lines = p.read_text().splitlines()
            for e in sorted(file_edits, key=lambda x: x["range"]["start"]["line"], reverse=True):
                r = e["range"]; l = r["start"]["line"]
                f_lines[l] = f_lines[l][:r["start"]["character"]] + e["newText"] + f_lines[l][r["end"]["character"]:]
            p.write_text("\n".join(f_lines))
        return "Rename applied via LSP."

def main():
    parser = argparse.ArgumentParser(description="Ultimate Safe Edit Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    r_parser = subparsers.add_parser("replace")
    r_parser.add_argument("file"); r_parser.add_argument("old"); r_parser.add_argument("new")
    
    rn_parser = subparsers.add_parser("rename")
    rn_parser.add_argument("file"); rn_parser.add_argument("symbol"); rn_parser.add_argument("new_name"); rn_parser.add_argument("--root", default=".")
    
    l_parser = subparsers.add_parser("lint")
    l_parser.add_argument("file")

    lsp_parser = subparsers.add_parser("lsp-start", help="Warm up LSP server for a language")
    lsp_parser.add_argument("lang", help="Language name (e.g. java, go, rust)")
    lsp_parser.add_argument("--root", default=".", help="Project root")

    args = parser.parse_args()
    editor = UltimateSafeEditor()
    try:
        if args.command == "replace": print(editor.smart_replace(args.file, args.old, args.new))
        elif args.command == "rename": print(editor.rename_symbol(args.file, args.symbol, args.new_name, args.root))
        elif args.command == "lint": print(editor.fix_lint(args.file))
        elif args.command == "lsp-start":
            lang_id = ALIASES.get(args.lang.lower())
            if not lang_id: print(f"❌ Language '{args.lang}' not supported."); return
            client = editor._get_lsp_client(lang_id, Path(args.root).resolve())
            if client: 
                client.initialize()
                print(f"✅ LSP for {lang_id} is warming up in background.")
            else: print(f"❌ LSP binary for {lang_id} not found.")
        else: parser.print_help()
    except Exception as e: print(f"FATAL: {e}")

if __name__ == "__main__":
    main()
