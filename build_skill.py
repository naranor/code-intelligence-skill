import zipfile
import os
from pathlib import Path

def build_skill():
    skill_name = "code-intelligence.skill"
    # Files essential for the skill to function within an agent environment
    include_files = [
        "safe_edit.py",
        "distiller.py",
        "SKILL.md",
        "README.md",
        "requirements.txt",
        "LICENSE",
        "ACKNOWLEDGMENTS.md"
    ]
    
    print(f"📦 Building {skill_name}...")
    
    with zipfile.ZipFile(skill_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in include_files:
            if os.path.exists(file):
                zipf.write(file)
                print(f"  + Added {file}")
            else:
                print(f"  ! Warning: {file} not found, skipping")
                
    print(f"✅ Done! Created {skill_name}")
    print(f"ℹ️ You can now load this file into your Gemini CLI or compatible agent.")

if __name__ == "__main__":
    build_skill()
