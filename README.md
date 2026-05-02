# Code Intelligence Skill for Gemini CLI

Universal, safe, and professional code modification and refactoring environment for AI agents.

## Features

- **Multi-language Safe Editing**: Built-in syntax verification for Python, Java, Go, C++, Rust, and more.
- **LSP Integration**: Professional project-wide refactoring (rename) using standard Language Servers (jdtls, gopls, rust-analyzer).
- **Lazy Pre-heating**: Start LSP servers in the background with automatic progress monitoring.
- **Output Distillation**: Keep your context window lean by distilling large command outputs.

## Tools Included

- `safe_edit.py`: The core engine for replacements and refactoring.
- `distiller_wrapper.py`: Command output compressor.

## Installation

1. Create a ZIP of this repository.
2. Rename extension to `.skill`.
3. Load into your Gemini CLI.

## Requirements

- Python 3.10+
- `tree-sitter` (optional, for non-Python syntax checks)
- `rope` (optional, for Python refactoring)
- Specific LSP servers for industrial refactoring (e.g., `gopls` for Go).

