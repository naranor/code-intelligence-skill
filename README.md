# Code Intelligence Skill for Gemini CLI and Claude Code

[![CI](https://github.com/naranor/code-intelligence-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/naranor/code-intelligence-skill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Universal, safe, and professional code modification and refactoring environment for AI agents. This skill enables AI agents to perform complex code manipulations with AST-level safety and project-wide type-aware refactoring.

Supports **Gemini CLI** and **Claude Code** out of the box, following the shared [agentskills.io](https://agentskills.io) standard.

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
- `install_skill.py`: Installer for Gemini CLI and Claude Code.

## Installation

### Automated Installation (Recommended)

The `install_skill.py` script handles all file placement and directory creation automatically. It supports both CLIs, both user and workspace scopes, and can install from a local source checkout or a downloaded `.skill` archive.

#### Install into both CLIs at once

```bash
# From a source checkout
python3 install_skill.py

# From a downloaded release archive
python3 install_skill.py --source code-intelligence.skill
```

#### Install only for Gemini CLI

```bash
python3 install_skill.py --target gemini-cli
```

After installation, confirm the skill is loaded:
```bash
# In a Gemini CLI session
/skills list
```

#### Install only for Claude Code

```bash
python3 install_skill.py --target claude-code
```

After installation, reload plugins in Claude Code:
```
/plugin reload
```

#### Install for the current workspace instead of your user account

```bash
python3 install_skill.py --scope workspace
```

#### Uninstall

```bash
python3 install_skill.py --target gemini-cli --uninstall
python3 install_skill.py --target claude-code --uninstall
```

#### Via Makefile

```bash
make install-gemini    # Gemini CLI, user scope
make install-claude    # Claude Code, user scope
make install-all       # Both CLIs, user scope
make uninstall-gemini  # Remove Gemini CLI installation
make uninstall-claude  # Remove Claude Code installation
```

#### Via console command (after `pip install -e .`)

```bash
install-skill                        # Both CLIs, user scope
install-skill --target gemini-cli    # Gemini CLI only
install-skill --target claude-code   # Claude Code only
```

---

### Install Locations

| Target | Scope | Directory |
|---|---|---|
| Gemini CLI | user | `~/.gemini/skills/code-intelligence/` |
| Gemini CLI | workspace | `.gemini/skills/code-intelligence/` |
| Claude Code | user | `~/.claude/plugins/code-intelligence/` |
| Claude Code | workspace | `.claude/plugins/code-intelligence/` |

---

### Manual Installation (Fallback)

If you prefer to install manually or are using a custom agent:

1. Copy `safe_edit.py`, `distiller.py`, and `SKILL.md` into your target skill directory.
2. Install dependencies: `pip install -r requirements.txt`.
3. Verify: `python3 safe_edit.py check-env`.

For **Gemini CLI** the skill directory structure should be:
```
~/.gemini/skills/code-intelligence/
├── SKILL.md
├── safe_edit.py
├── distiller.py
└── requirements.txt
```

For **Claude Code** the plugin structure should be:
```
~/.claude/plugins/code-intelligence/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── code-intelligence/
│       └── SKILL.md
├── safe_edit.py
├── distiller.py
└── requirements.txt
```

---

### Prerequisites

- Python 3.10+ on `PATH` as `python3`
- Install optional dependencies for extended language support:
  ```bash
  pip install -r requirements.txt
  ```
- Install optional LSP servers for type-aware rename:
  - Go: `go install golang.org/x/tools/gopls@latest`
  - Java: install `jdtls`
  - Rust: install `rust-analyzer`
  - C/C++: install `clangd`

### Upgrade

Re-run the installer to overwrite an existing installation:
```bash
python3 install_skill.py --target all
```

### Verification

```bash
python3 safe_edit.py check-env
```

---

### Using Pre-built Skill Package

Download the latest `code-intelligence.skill` from the **GitHub Releases** page and install from the archive:

```bash
python3 install_skill.py --source /path/to/code-intelligence.skill
```

### Building from Source

```bash
# Build the .skill archive
make build
# Verify the artifact
make verify
```

### For Developers (System-wide CLI)

```bash
pip install -e .
safe-edit check-env
install-skill --help
```

---

## Migrating from a Previous Manual Install

If you previously copied `safe_edit.py` / `distiller.py` directly into `.gemini/skills/` or a custom path, your existing setup will continue to work. To switch to the managed layout, run:

```bash
python3 install_skill.py --target gemini-cli
```

The installer will create the canonical `~/.gemini/skills/code-intelligence/` directory without affecting other skills.

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
