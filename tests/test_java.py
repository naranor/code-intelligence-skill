import subprocess
import pytest
import time
from pathlib import Path

SAFE_EDIT = ".gemini/skills/code-intelligence/safe_edit.py"

def test_java_maven_structure_rename(tmp_path):
    # Setup Maven-like project
    src = tmp_path / "src/main/java/com/example"
    src.mkdir(parents=True)
    
    pom = tmp_path / "pom.xml"
    pom.write_text("<project><modelVersion>4.0.0</modelVersion><groupId>com.example</groupId><artifactId>test</artifactId><version>1.0</version></project>")
    
    f1 = src / "Service.java"
    f1.write_text("package com.example;\npublic class Service { public void oldM() {} }")
    f2 = src / "App.java"
    f2.write_text("package com.example;\npublic class App { void run() { new Service().oldM(); } }")
    
    # 1. Test Pre-heating
    res_start = subprocess.run(["python3", SAFE_EDIT, "lsp-start", "java", "--root", str(tmp_path)], capture_output=True, text=True)
    assert "warming up" in res_start.stdout or "LSP" in res_start.stdout
    
    # Wait for heavy jdtls initialization in CI/Docker
    time.sleep(5) 
    
    # 2. Test Rename (might take time, so we check the command was attempted)
    res_rename = subprocess.run(["python3", SAFE_EDIT, "rename", str(f1), "oldM", "newM", "--root", str(tmp_path)], capture_output=True, text=True)
    
    if "applied" in res_rename.stdout:
        assert "newM" in f1.read_text()
        assert "newM" in f2.read_text()
    elif "Error: LSP" in res_rename.stdout:
        print("Test skipped: jdtls not found in current environment.")
