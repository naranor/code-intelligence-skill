"""
install_skill.py — Installer for the Code Intelligence Skill.

Supports Gemini CLI and Claude Code as installation targets.

Usage:
    python3 install_skill.py [options]

Options:
    --target    gemini-cli | claude-code | all  (default: all)
    --scope     user | workspace                (default: user)
    --source    path to source dir or .skill archive  (default: current dir)
    --uninstall Remove a previously installed skill

Examples:
    # Install to both CLIs (user scope):
    python3 install_skill.py

    # Install only for Claude Code in current workspace:
    python3 install_skill.py --target claude-code --scope workspace

    # Install from a downloaded .skill archive:
    python3 install_skill.py --source code-intelligence.skill

    # Uninstall from Gemini CLI:
    python3 install_skill.py --target gemini-cli --uninstall
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_NAME = "code-intelligence"
REQUIRED_FILES = ["safe_edit.py", "distiller.py", "SKILL.md"]
OPTIONAL_FILES = ["requirements.txt", "LICENSE", "ACKNOWLEDGMENTS.md"]

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def get_gemini_skills_dir(scope: str) -> Path:
    """Return the Gemini CLI skills directory for the given scope.

    Gemini CLI checks these locations (lowest → highest precedence):
      user:      ~/.gemini/skills/   or  ~/.agents/skills/
      workspace: .gemini/skills/     or  .agents/skills/
    We use the primary path (*.gemini*) for installation.
    """
    if scope == "user":
        return Path.home() / ".gemini" / "skills" / SKILL_NAME
    return Path.cwd() / ".gemini" / "skills" / SKILL_NAME


def get_claude_plugin_dir(scope: str) -> Path:
    """Return the Claude Code plugin directory for the given scope.

    Claude Code loads plugins from:
      user:      ~/.claude/plugins/<name>/
      workspace: .claude/plugins/<name>/
    """
    if scope == "user":
        return Path.home() / ".claude" / "plugins" / SKILL_NAME
    return Path.cwd() / ".claude" / "plugins" / SKILL_NAME


# ---------------------------------------------------------------------------
# Source handling (directory or .skill ZIP)
# ---------------------------------------------------------------------------

def resolve_source(source: str) -> Path:
    """Return the path to the unpacked skill source directory.

    If *source* is a `.skill` ZIP archive it is extracted to a temp directory
    and that path is returned.  Otherwise the path is validated as a directory
    that contains the required files and returned as-is.
    """
    src = Path(source).resolve()

    if not src.exists():
        _die(f"Source not found: {src}")

    if src.is_file() and src.suffix == ".skill":
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="code-intelligence-install-"))
        print(f"  📦 Extracting {src.name} → {tmp}")
        with zipfile.ZipFile(src, "r") as zf:
            root = tmp.resolve()
            for member in zf.infolist():
                name = member.filename.replace("\\", "/")
                dest_path = (root / name).resolve()
                if dest_path != root and root not in dest_path.parents:
                    _die(f"Unsafe path in archive: {member.filename}")
            zf.extractall(tmp)
        return tmp

    if src.is_dir():
        missing = [f for f in REQUIRED_FILES if not (src / f).exists()]
        if missing:
            _die(f"Source directory is missing required files: {missing}")
        return src

    _die(f"Source must be a directory or a .skill archive, got: {src}")


# ---------------------------------------------------------------------------
# Gemini CLI install
# ---------------------------------------------------------------------------

def install_gemini(source_dir: Path, scope: str) -> Path:
    """Install the skill for Gemini CLI and return the install directory."""
    dest = get_gemini_skills_dir(scope)
    print(f"\n🔧 Installing for Gemini CLI → {dest}")
    dest.mkdir(parents=True, exist_ok=True)

    _copy_files(source_dir, dest, REQUIRED_FILES + OPTIONAL_FILES)

    # Gemini CLI loads skills from a directory named after the skill.
    # The SKILL.md at the root of the skill directory is the entry point.
    verify_install("gemini-cli", dest)
    return dest


def uninstall_gemini(scope: str) -> None:
    """Remove the Gemini CLI skill installation."""
    dest = get_gemini_skills_dir(scope)
    print(f"\n🗑️  Removing Gemini CLI installation: {dest}")
    if dest.exists():
        shutil.rmtree(dest)
        print("  ✅ Removed.")
    else:
        print("  ℹ️  Not installed — nothing to remove.")


# ---------------------------------------------------------------------------
# Claude Code install
# ---------------------------------------------------------------------------

_CLAUDE_PLUGIN_JSON_TEMPLATE = """\
{{
  "name": "{skill_name}",
  "description": "Universal, safe, and professional code modification and refactoring environment for 50+ languages.",
  "version": "{version}"
}}
"""

def _read_version(source_dir: Path) -> str:
    """Try to read version from README.md badge or fall back to '1.0.0'."""
    readme = source_dir / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        import re
        m = re.search(r"version[^\d]*(\d+\.\d+\.\d+)", content, re.IGNORECASE)
        if m:
            return m.group(1)
    return "1.0.0"


def install_claude(source_dir: Path, scope: str) -> Path:
    """Install the skill as a Claude Code plugin and return the install directory."""
    dest = get_claude_plugin_dir(scope)
    print(f"\n🔧 Installing for Claude Code → {dest}")

    # Plugin manifest directory
    manifest_dir = dest / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    # Plugin manifest
    version = _read_version(source_dir)
    plugin_json = manifest_dir / "plugin.json"
    plugin_json.write_text(
        _CLAUDE_PLUGIN_JSON_TEMPLATE.format(
            skill_name=SKILL_NAME, version=version
        ),
        encoding="utf-8",
    )
    print(f"  + Created .claude-plugin/plugin.json (v{version})")

    # Skill entry point expected by Claude Code's plugin skill loader
    skill_dest = dest / "skills" / SKILL_NAME
    skill_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_dir / "SKILL.md", skill_dest / "SKILL.md")
    print(f"  + Copied SKILL.md → skills/{SKILL_NAME}/SKILL.md")

    # Runtime scripts at plugin root (accessible from skill context)
    _copy_files(source_dir, dest, ["safe_edit.py", "distiller.py"] + OPTIONAL_FILES)

    verify_install("claude-code", dest)
    return dest


def uninstall_claude(scope: str) -> None:
    """Remove the Claude Code plugin installation."""
    dest = get_claude_plugin_dir(scope)
    print(f"\n🗑️  Removing Claude Code installation: {dest}")
    if dest.exists():
        shutil.rmtree(dest)
        print("  ✅ Removed.")
    else:
        print("  ℹ️  Not installed — nothing to remove.")


# ---------------------------------------------------------------------------
# Post-install verification
# ---------------------------------------------------------------------------

def verify_install(target: str, install_dir: Path) -> None:
    """Verify that required files are present in *install_dir*."""
    if target == "claude-code":
        required = [
            install_dir / ".claude-plugin" / "plugin.json",
            install_dir / "skills" / SKILL_NAME / "SKILL.md",
            install_dir / "safe_edit.py",
            install_dir / "distiller.py",
        ]
    else:  # gemini-cli
        required = [
            install_dir / "SKILL.md",
            install_dir / "safe_edit.py",
            install_dir / "distiller.py",
        ]

    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _die(f"Post-install verification failed. Missing files:\n  " + "\n  ".join(missing))

    print(f"  ✅ Verification passed ({len(required)} required files present).")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _copy_files(src_dir: Path, dest_dir: Path, filenames: list) -> None:
    for name in filenames:
        src = src_dir / name
        if src.exists():
            dest = dest_dir / name
            shutil.copy2(src, dest)
            print(f"  + Copied {name}")
        else:
            print(f"  · Skipping {name} (not found in source)")


def _die(message: str) -> None:
    print(f"\n❌ Error: {message}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Install the Code Intelligence Skill into Gemini CLI or Claude Code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--target",
        choices=["gemini-cli", "claude-code", "all"],
        default="all",
        help="Target AI CLI to install into (default: all)",
    )
    parser.add_argument(
        "--scope",
        choices=["user", "workspace"],
        default="user",
        help="Install for current user (default) or current workspace only",
    )
    parser.add_argument(
        "--source",
        default=".",
        help="Path to source directory or .skill archive (default: current directory)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove a previously installed skill instead of installing",
    )

    args = parser.parse_args(argv)

    if args.uninstall:
        print(f"🗑️  Uninstalling Code Intelligence Skill (scope: {args.scope})")
        if args.target in ("gemini-cli", "all"):
            uninstall_gemini(args.scope)
        if args.target in ("claude-code", "all"):
            uninstall_claude(args.scope)
        print("\n✅ Uninstall complete.")
        return

    print(f"📦 Installing Code Intelligence Skill (target: {args.target}, scope: {args.scope})")
    source_dir = resolve_source(args.source)

    installed = []
    if args.target in ("gemini-cli", "all"):
        dest = install_gemini(source_dir, args.scope)
        installed.append(("Gemini CLI", dest))
    if args.target in ("claude-code", "all"):
        dest = install_claude(source_dir, args.scope)
        installed.append(("Claude Code", dest))

    print("\n✅ Installation complete!")
    for cli, path in installed:
        print(f"   {cli}: {path}")

    print("\nNext steps:")
    req_paths = [path / "requirements.txt" for _, path in installed if (path / "requirements.txt").exists()]
    if req_paths:
        print("  1. Install Python dependencies:")
        for p in req_paths:
            print(f"     pip install -r {p}")
    else:
        print("  1. Install Python dependencies:  pip install -r requirements.txt")
    print("  2. Verify the environment:        python3 safe_edit.py check-env")
    if any(cli == "Claude Code" for cli, _ in installed):
        print("  3. Claude Code: restart the CLI or run /plugin reload")
    if any(cli == "Gemini CLI" for cli, _ in installed):
        print("  3. Gemini CLI:  run /skills list to confirm the skill is loaded")


if __name__ == "__main__":
    main()
