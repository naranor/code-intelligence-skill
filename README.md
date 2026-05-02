# Code Intelligence Skill for Gemini CLI

[![CI](https://github.com/your-username/code-intelligence-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/code-intelligence-skill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Universal, safe, and professional code modification and refactoring environment for AI agents. This skill enables AI agents to perform complex code manipulations with AST-level safety and project-wide type-aware refactoring.

### The Problem It Solves

AI agents frequently make mistakes when editing code, often breaking the file's syntax with unmatched brackets, missing colons, or indentation errors. These failures trigger a costly and frustrating cycle: the agent attempts to fix the error, often unsuccessfully; it might even resort to overwriting the entire file, which can lead to the loss of important comments or the oversimplification of complex logic. These issues are sometimes only caught much later during testing or at runtime, leading to a massive waste of tokens and session steps as the agent struggles to recover.

**`safe_edit` solves this problem at the source.** By performing mandatory AST (Abstract Syntax Tree) verification *before* any changes are committed to disk, it ensures that the file is never left in a broken state. If an edit would violate the language's syntax, the tool returns a clear error, and the original file remains untouched. This guarantees structural integrity, prevents code loss, and significantly reduces token consumption by stopping the "syntax-fix-break" loop before it starts.

## Features

- **Multi-language Safe Editing**: Built-in syntax verification for Python, Java, Go, C++, Rust, and more.
- **LSP Integration**: Professional project-wide refactoring (rename) using standard Language Servers (`jdtls`, `gopls`, `rust-analyzer`).
- **Lazy Pre-heating**: Start LSP servers in the background with automatic progress monitoring.
- **Output Distillation**: Keep your context window lean by distilling large command outputs.

## Tools Included

- `safe_edit.py`: The core engine for replacements and refactoring.
- `distiller.py`: Command output compressor and filter.

## Installation

There are several ways to install and use the Code Intelligence Skill, depending on your environment and needs.

### 1. Manual Installation (Portable Scripts)
Best for custom agents or simple environments.
- Copy `safe_edit.py` and `distiller.py` directly into your agent's skills folder (e.g., `.agents/skills/` or `.gemini/skills/`).
- Ensure you have the dependencies installed: `pip install -r requirements.txt`.

### 2. Using Pre-built Skill Package
Best for Gemini CLI and compatible agents.
- Download the latest `code-intelligence.skill` from the **GitHub Releases** page.
- Load the downloaded file into your agent's configuration.

### 3. Building from Source
If you want to build the skill package yourself from the latest source code:

**Option A: Using Makefile (Recommended)**
```bash
make build
```
This creates `code-intelligence.skill` in the root directory.

**Option B: Using Python Script**
If `make` is not available on your system:
```bash
python3 build_skill.py
```

### 4. For Developers (System-wide CLI)
If you want to use `safe-edit` and `distill` as global commands in your terminal:
```bash
pip install -e .
# Verification
safe-edit check-env
```

## Usage

### Environment Diagnostics
```bash
python3 safe_edit.py check-env
```

### Safe Replace
```bash
python3 safe_edit.py replace <file> "<old_text>" "<new_text>"
```

### Type-Aware Rename (LSP)
```bash
python3 safe_edit.py lsp-start go  # Pre-heat LSP
python3 safe_edit.py rename <file> <symbol> <new_name> --root <project_root>
```

## Internal Architecture

The tool uses a **Modular Engine** system within a single file to maintain portability:
- **PythonEngine**: Uses `ast` for verification and `rope` for refactoring.
- **GoEngine**: Uses `tree-sitter` and native `gopls` integration.
- **LSP Engines**: Generic support for Java, Rust, C++ via standard JSON-RPC.

## Requirements

- Python 3.10+
- `tree-sitter` (for multi-language syntax checks)
- `rope` (for Python refactoring)
- Specific LSP servers for industrial refactoring (e.g., `gopls` for Go).

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

This project uses several open-source components. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for full details and license texts.
- **tree-sitter**: MIT
- **rope**: LGPLv3
- **pytest**: MIT
