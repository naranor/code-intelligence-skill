import subprocess
import pytest
from pathlib import Path

SAFE_EDIT = "safe_edit.py"

def test_python_replace_sunny(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("def hello(): print('old')")
    res = subprocess.run(["python3", SAFE_EDIT, "replace", str(f), "print('old')", "print('new')"], capture_output=True, text=True)
    assert "Successfully updated" in res.stdout
    assert "print('new')" in f.read_text()

def test_python_replace_rainy(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("def hello(): pass")
    # Intentional syntax error
    res = subprocess.run(["python3", SAFE_EDIT, "replace", str(f), "pass", "pass("], capture_output=True, text=True)
    assert "Syntax error" in res.stdout
    assert "pass(" not in f.read_text()

def test_python_rename_global(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    f1 = pkg / "m1.py"
    f1.write_text("def target(): pass")
    f2 = pkg / "m2.py"
    f2.write_text("from .m1 import target; target()")
    
    res = subprocess.run(["python3", SAFE_EDIT, "rename", str(f1), "target", "renamed", "--root", str(tmp_path)], capture_output=True, text=True)
    assert "Renamed" in res.stdout
    assert "def renamed()" in f1.read_text()
    assert "import renamed" in f2.read_text() or "renamed()" in f2.read_text()
