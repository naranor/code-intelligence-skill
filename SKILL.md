# Code Intelligence Skill (Universal Edition)

This skill provides a unified, safe, and professional environment for code modification and refactoring across 50+ languages using **AST verification** and **LSP (Language Server Protocol)**.

### 🛡️ Why use safe_edit? (Core Mandate)
Standard file edits often lead to syntax breakage, causing you (the agent) to enter a "fix-it" loop that wastes tokens and can lead to permanent code loss or oversimplification if you decide to overwrite the entire file.

`safe_edit.py` prevents this by:
1. **Validating changes against the AST** before saving.
2. **Aborting the save** if the syntax is broken.
3. **Preserving your context** by preventing unnecessary debugging steps.

## 1. Environment Diagnostics

Before starting intensive work, verify your environment to see which languages and tools are supported.
- **Command**: `python3 safe_edit.py check-env`
- **What it checks**: Presence of `tree-sitter`, `rope`, and active Language Servers (gopls, jdtls, etc.).

## 2. Safe Multi-Language Editing

Use `safe_edit.py` for ALL code modifications. It prevents syntax breakage by verifying code structure before saving.

### A. Pre-heating (LSP Warming)
For heavy languages (Java, Rust, C++), start the language server early to build the index in background.
- **Command**: `python3 safe_edit.py lsp-start <lang> [--root <project_root>]`
- **Example**: `python3 safe_edit.py lsp-start java`
- **When to use**: At the beginning of the implementation phase if you plan to do refactoring.

### B. Smart Replace (Atomic & Verified)
Replaces unique text blocks with mandatory syntax verification.
- **Command**: `python3 safe_edit.py replace <file> "<old>" "<new>"`
- **Engines**: 
    - **Python**: Uses builtin `ast` (No dependencies required).
    - **Go/Java/Others**: Uses `tree-sitter` grammars if available.
- **Rule**: `<old>` text MUST be unique in the file to avoid ambiguity.

### C. Industrial Refactoring (Rename)
Renames symbols across the entire project with full type-awareness.
- **Command**: `python3 safe_edit.py rename <file> <symbol> <new_name> [--root <project_root>]`
- **Engines**:
    - **Python**: Uses `Rope` library.
    - **Go**: Uses native `gopls` CLI for maximum speed and reliability.
    - **Java/Rust/CPP**: Uses generic **LSP JSON-RPC** client.
- **Behavior**: Updates the definition and ALL call-sites/references in the project.

## 3. Token Saving (Output Distillation)

Always wrap voluminous commands with `distiller.py` to keep your context lean.
- **Example**: `python3 distiller.py <tool_name> <command...>`

## Mandates for Agents

1.  **NO SED**: Never use `sed` or `grep -v` for code editing. Use `safe_edit.py replace`.
2.  **CHECK ENV FIRST**: Run `check-env` at the start of a session to understand your capabilities.
3.  **LSP FIRST**: If working on a Java or Go project, always run `lsp-start` first to ensure fast and reliable refactoring.
4.  **VERIFY ALWAYS**: `safe_edit.py replace` automatically verifies syntax. If it fails, do NOT attempt to force the write via other tools.
5.  **INSTALL IF MISSING**: If `check-env` shows missing dependencies (e.g., `rope` or `tree-sitter`), you are PERMITTED to run `pip install` to enable them.
