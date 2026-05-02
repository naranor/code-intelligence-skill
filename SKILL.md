# Code Intelligence Skill (Universal Edition)

This skill provides a unified, safe, and professional environment for code modification and refactoring across 50+ languages using **AST verification** and **LSP (Language Server Protocol)**.

## 1. Safe Multi-Language Editing

Use `safe_edit.py` for ALL code modifications. It prevents syntax breakage by verifying code structure before saving.

### A. Pre-heating (LSP Warming)
For heavy languages (Java, Rust, C++), start the language server early to build the index in background.
- **Command**: `python3 .gemini/skills/code-intelligence/safe_edit.py lsp-start <lang>`
- **Example**: `python3 .gemini/skills/code-intelligence/safe_edit.py lsp-start java`
- **When to use**: At the beginning of the implementation phase if you plan to do refactoring.

### B. Smart Replace (Atomic & Verified)
Replaces unique text blocks with mandatory syntax verification.
- **Command**: `python3 .gemini/skills/code-intelligence/safe_edit.py replace <file> "<old>" "<new>"`
- **Engines**: 
    - **Python**: Uses builtin `ast` (No dependencies required).
    - **Go/Java/Others**: Uses `tree-sitter` grammars (Ensures bracket/keyword integrity).
- **Rule**: `<old>` text MUST be unique in the file to avoid ambiguity.

### C. Industrial Refactoring (Rename)
Renames symbols across the entire project with full type-awareness.
- **Command**: `python3 .gemini/skills/code-intelligence/safe_edit.py rename <file> <symbol> <new_name> [--root <project_root>]`
- **Engines**:
    - **Python**: Uses `Rope` library.
    - **Go/Java/Rust**: Uses native **LSP servers** (gopls, jdtls, rust-analyzer).
- **Behavior**: Updates the definition and ALL call-sites/references in the project.

### D. Syntax Linting
Verifies file validity and attempts automated fixes.
- **Command**: `python3 .gemini/skills/code-intelligence/safe_edit.py lint <file>`
- **Behavior**: Detects syntax errors and applies formatters (Ruff/GoFmt/Black) if available.

## 2. Token Saving (Output Distillation)

Always wrap voluminous commands with `distiller_wrapper.py` to keep your context lean.
- **Example**: `python3 .gemini/skills/code-intelligence/distiller_wrapper.py <command>`

## Mandates for Agents

1.  **NO SED**: Never use `sed` or `grep -v` for code editing. Use `safe_edit.py replace`.
2.  **LSP FIRST**: If working on a Java or Go project, always run `lsp-start` first to ensure fast and reliable refactoring.
3.  **VERIFY ALWAYS**: After any manual `write_file` or `replace`, you MUST run `safe_edit.py lint` to confirm you haven't broken the AST.
4.  **RENAME FOR REFACTOR**: If you need to rename a function or class, use `rename` instead of multiple `replace` calls. It's safer and type-aware.
5.  **INSTALL IF MISSING**: If `safe_edit.py` tells you a grammar (e.g., `tree-sitter-java`) is missing, you are PERMITTED to run `pip install` to enable it.
