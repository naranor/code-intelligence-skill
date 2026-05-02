import sys
import os
import ast
import argparse
import subprocess
import json
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any, Type

# --- Core Data Structures ---

@dataclass
class Position:
    line: int
    character: int

@dataclass
class Range:
    start: Position
    end: Position

@dataclass
class TextEdit:
    range: Range
    new_text: str

# --- Language Engines (Extensibility) ---

class BaseEngine:
    """Base class for language-specific logic."""
    def verify_syntax(self, code: str) -> bool:
        return True  # Default to permissive

    def get_lsp_command(self) -> Optional[List[str]]:
        return None

    def perform_rename(self, file_path: Path, symbol: str, new_name: str, root_path: Path) -> str:
        return "Rename not supported for this language."

class PythonEngine(BaseEngine):
    def verify_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            print(f"❌ Python Syntax Error: {e}")
            return False

    def perform_rename(self, file_path: Path, symbol: str, new_name: str, root_path: Path) -> str:
        try:
            from rope.base.project import Project
            from rope.refactor.rename import Rename
            project = Project(str(root_path))
            res = project.get_resource(str(file_path.relative_to(root_path)))
            offset = res.read().find(symbol)
            if offset == -1: return "Error: Symbol not found in file."
            project.do(Rename(project, res, offset).get_changes(new_name))
            project.close()
            return f"Renamed '{symbol}' to '{new_name}' (Python/Rope)."
        except ImportError:
            return "Error: 'rope' library not installed for Python refactoring."
        except Exception as e:
            return f"Python rename failed: {e}"

class TreeSitterEngine(BaseEngine):
    def __init__(self, lang_id: str, lsp_bin: Optional[str] = None):
        self.lang_id = lang_id
        self.lsp_bin = lsp_bin

    def verify_syntax(self, code: str) -> bool:
        try:
            from tree_sitter import Language, Parser
            mod_name = f"tree_sitter_{self.lang_id}"
            mod = __import__(mod_name)
            parser = Parser()
            parser.set_language(Language(mod.language(), self.lang_id))
            tree = parser.parse(bytes(code, "utf8"))
            return not tree.root_node.has_error
        except ImportError:
            # If tree-sitter or grammar is missing, we fallback to True but warn
            # print(f"⚠️ tree-sitter-{self.lang_id} not found, skipping AST check.")
            return True
        except Exception as e:
            print(f"⚠️ Tree-sitter error: {e}")
            return True

    def get_lsp_command(self) -> Optional[List[str]]:
        if not self.lsp_bin: return None
        # Look in PATH and common local paths
        possible = [self.lsp_bin, os.path.expanduser(f"~/go/bin/{self.lsp_bin}"), os.path.expanduser(f"~/.local/bin/{self.lsp_bin}")]
        for p in possible:
            try:
                if subprocess.run(["which", p], capture_output=True).returncode == 0: return [p]
                if os.path.isfile(p) and os.access(p, os.X_OK): return [p]
            except: continue
        return None

class GoEngine(TreeSitterEngine):
    def perform_rename(self, file_path: Path, symbol: str, new_name: str, root_path: Path) -> str:
        # Go has a very reliable CLI tool for rename via gopls
        lsp_cmd = self.get_lsp_command()
        if not lsp_cmd: return "Error: gopls not found."
        
        content = file_path.read_text()
        lines = content.splitlines()
        pos = next(((i, line.find(symbol)) for i, line in enumerate(lines) if line.find(symbol) != -1), None)
        if not pos: return "Error: Symbol not found."
        
        # gopls rename -w file.go:line:col newname
        res = subprocess.run([lsp_cmd[0], "rename", "-w", f"{file_path}:{pos[0]+1}:{pos[1]+1}", new_name], capture_output=True, text=True)
        return "Rename successful (Go/gopls)." if res.returncode == 0 else f"Gopls Error: {res.stderr}"

# --- LSP Client ---

class MinimalLspClient:
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
        self.process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0
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

# --- Main Editor ---

class UltimateSafeEditor:
    def __init__(self):
        self.engines: Dict[str, BaseEngine] = {
            ".py": PythonEngine(),
            ".go": GoEngine("go", "gopls"),
            ".java": TreeSitterEngine("java", "jdtls"),
            ".rs": TreeSitterEngine("rust", "rust-analyzer"),
            ".cpp": TreeSitterEngine("cpp", "clangd"),
            ".c": TreeSitterEngine("c", "clangd"),
        }
        self._lsp_clients: Dict[str, MinimalLspClient] = {}

    def get_engine(self, ext: str) -> BaseEngine:
        return self.engines.get(ext.lower(), BaseEngine())

    def smart_replace(self, file_path: str, old: str, new: str) -> str:
        fp = Path(file_path).resolve()
        if not fp.exists(): return f"Error: File {file_path} not found."
        content = fp.read_text(encoding="utf-8")
        if content.count(old) != 1: return f"Error: Match not unique ({content.count(old)} found)."
        
        new_content = content.replace(old, new)
        engine = self.get_engine(fp.suffix)
        if not engine.verify_syntax(new_content): return "Aborting: Syntax error detected."
        
        fp.write_text(new_content, encoding="utf-8")
        return f"Successfully updated {file_path}."

    def rename_symbol(self, file_path: str, symbol: str, new_name: str, root_path: str = ".") -> str:
        fp = Path(file_path).resolve()
        rp = Path(root_path).resolve()
        engine = self.get_engine(fp.suffix)
        
        # Try engine-specific rename first (like Rope or Go CLI)
        res = engine.perform_rename(fp, symbol, new_name, rp)
        if "Error" not in res and "not supported" not in res: return res

        # Fallback to Generic LSP Client
        lsp_cmd = engine.get_lsp_command()
        if not lsp_cmd: return res # Return the engine error

        client = self._lsp_clients.get(fp.suffix)
        if not client:
            client = MinimalLspClient(lsp_cmd, rp, fp.suffix[1:])
            self._lsp_clients[fp.suffix] = client
        
        content = fp.read_text()
        lines = content.splitlines()
        pos = next(((i, line.find(symbol)) for i, line in enumerate(lines) if line.find(symbol) != -1), None)
        if not pos: return "Error: Symbol not found in file."

        edit = client.rename(fp, pos[0], pos[1], new_name)
        if not edit: return "LSP Error: No edits received."
        
        # Apply edits
        changes = edit.get("changes", {})
        for uri, file_edits in changes.items():
            p = Path(uri.replace("file://", ""))
            f_lines = p.read_text().splitlines()
            # Sort edits in reverse order to keep indices valid
            for e in sorted(file_edits, key=lambda x: x["range"]["start"]["line"], reverse=True):
                r = e["range"]; l = r["start"]["line"]
                f_lines[l] = f_lines[l][:r["start"]["character"]] + e["newText"] + f_lines[l][r["end"]["character"]:]
            p.write_text("\n".join(f_lines))
        return "Rename applied via LSP."

    def check_env(self):
        print("--- Code Intelligence Environment Check ---")
        # Python
        try: import rope; print("✅ Python: 'rope' installed.")
        except: print("❌ Python: 'rope' missing (refactoring disabled).")
        # Tree-sitter
        try: import tree_sitter; print("✅ Tree-sitter: Core library installed.")
        except: print("❌ Tree-sitter: Core library missing (AST checks disabled).")
        # Engines
        for ext, engine in self.engines.items():
            if isinstance(engine, TreeSitterEngine):
                lsp = engine.get_lsp_command()
                status = f"✅ LSP: {lsp[0]}" if lsp else "❌ LSP: missing"
                print(f"Language {ext}: {status}")

def main():
    parser = argparse.ArgumentParser(description="Ultimate Safe Edit Tool (Modular Edition)")
    subparsers = parser.add_subparsers(dest="command")
    
    r_parser = subparsers.add_parser("replace")
    r_parser.add_argument("file"); r_parser.add_argument("old"); r_parser.add_argument("new")
    
    rn_parser = subparsers.add_parser("rename")
    rn_parser.add_argument("file"); rn_parser.add_argument("symbol"); rn_parser.add_argument("new_name"); rn_parser.add_argument("--root", default=".")
    
    subparsers.add_parser("check-env")

    lsp_parser = subparsers.add_parser("lsp-start", help="Warm up LSP server for a language")
    lsp_parser.add_argument("lang"); lsp_parser.add_argument("--root", default=".")

    args = parser.parse_args()
    editor = UltimateSafeEditor()
    
    try:
        if args.command == "replace": print(editor.smart_replace(args.file, args.old, args.new))
        elif args.command == "rename": print(editor.rename_symbol(args.file, args.symbol, args.new_name, args.root))
        elif args.command == "check-env": editor.check_env()
        elif args.command == "lsp-start":
            ext = f".{args.lang}"
            engine = editor.get_engine(ext)
            cmd = engine.get_lsp_command()
            if cmd:
                client = MinimalLspClient(cmd, Path(args.root).resolve(), args.lang)
                client.initialize()
                print(f"✅ LSP for {args.lang} is warming up.")
            else: print(f"❌ LSP for {args.lang} not found.")
        else: parser.print_help()
    except Exception as e:
        print(f"FATAL: {e}")

if __name__ == "__main__":
    main()
