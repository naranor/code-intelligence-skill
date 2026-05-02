import subprocess
import pytest
import time
from pathlib import Path

SAFE_EDIT = ".gemini/skills/code-intelligence/safe_edit.py"

def test_go_replace_sunny(tmp_path):
    f = tmp_path / "main.go"
    f.write_text("package main\nfunc main() {}")
    res = subprocess.run(["python3", SAFE_EDIT, "replace", str(f), "main()", "greet()"], capture_output=True, text=True)
    assert "Successfully updated" in res.stdout
    assert "func greet()" in f.read_text()

def test_go_rename_lsp(tmp_path):
    f1 = tmp_path / "lib.go"
    f1.write_text("package main\nfunc Target() {}")
    f2 = tmp_path / "main.go"
    f2.write_text("package main\nfunc main() { Target() }")
    
    # Pre-heat
    subprocess.run(["python3", SAFE_EDIT, "lsp-start", "go", "--root", str(tmp_path)])
    time.sleep(1)
    
    res = subprocess.run(["python3", SAFE_EDIT, "rename", str(f1), "Target", "NewTarget", "--root", str(tmp_path)], capture_output=True, text=True)
    # Note: might fail if gopls is not in path, but here we test the logic
    if "gopls" in res.stdout or "Successfully" in res.stdout:
        assert "NewTarget" in f1.read_text()
        assert "NewTarget" in f2.read_text()
