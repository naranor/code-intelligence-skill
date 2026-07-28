import zipfile
import os
import sys
from pathlib import Path

SKILL_NAME = "code-intelligence.skill"
REQUIRED_FILES = ["safe_edit.py", "distiller.py", "SKILL.md"]
INCLUDE_FILES = [
    "safe_edit.py",
    "distiller.py",
    "SKILL.md",
    "README.md",
    "requirements.txt",
    "LICENSE",
    "ACKNOWLEDGMENTS.md",
]


def verify_artifact(skill_path: str) -> bool:
    """Verify that a .skill archive contains all required files.

    Returns True if the artifact is valid, False otherwise.
    Prints a status line for each required file.
    """
    path = Path(skill_path)
    if not path.exists():
        print(f"❌ Artifact not found: {skill_path}", file=sys.stderr)
        return False

    print(f"\n🔍 Verifying artifact: {skill_path}")
    ok = True
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        for required in REQUIRED_FILES:
            if required in names:
                print(f"  ✅ {required}")
            else:
                print(f"  ❌ MISSING: {required}")
                ok = False

    if ok:
        print("✅ Artifact integrity check passed.")
    else:
        print("❌ Artifact integrity check FAILED.", file=sys.stderr)
    return ok


def build_skill():
    print(f"📦 Building {SKILL_NAME}...")

    with zipfile.ZipFile(SKILL_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in INCLUDE_FILES:
            if os.path.exists(file):
                zipf.write(file)
                print(f"  + Added {file}")
            else:
                print(f"  ! Warning: {file} not found, skipping")

    print(f"✅ Done! Created {SKILL_NAME}")
    print("ℹ️  You can now load this file into your Gemini CLI or Claude Code.")

    if not verify_artifact(SKILL_NAME):
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        target = sys.argv[2] if len(sys.argv) > 2 else SKILL_NAME
        sys.exit(0 if verify_artifact(target) else 1)
    build_skill()

