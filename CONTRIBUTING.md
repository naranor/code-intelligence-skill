# Contributing to Code Intelligence Skill

Thank you for your interest in improving the Code Intelligence Skill! This document provides guidelines for contributing to the project.

## Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/naranor/code-intelligence-skill.git
   cd code-intelligence-skill
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[test]"
   ```

## Running Tests

We use `pytest` for testing. You can run all tests using:

```bash
pytest
```

This runs:
- `tests/test_python.py` — safe_edit unit tests (Python engine)
- `tests/test_installer.py` — installer path resolution and file layout tests

To run a specific test file:
```bash
pytest tests/test_python.py
pytest tests/test_installer.py
```

Note: Some tests for Go and Java require the respective Language Servers (`gopls`, `jdtls`) to be installed on your system.

## Testing the Installer

The installer (`install_skill.py`) uses `monkeypatch` to redirect install directories to temporary paths, so tests are safe to run in any environment and do not write to your home directory.

To manually test the installer end-to-end:

```bash
# Install to both CLIs (user scope)
python3 install_skill.py

# Install to a custom workspace path
python3 install_skill.py --scope workspace

# Install from a built archive
make build
python3 install_skill.py --source code-intelligence.skill

# Uninstall
python3 install_skill.py --uninstall
```

## Building the Skill Archive

```bash
make build    # Creates code-intelligence.skill
make verify   # Validates the archive contains all required files
```

## Pull Request Process

1. Create a new branch for your feature or bugfix.
2. Ensure all tests pass locally (`pytest`).
3. Add new tests if you are adding functionality or fixing a bug.
4. Update the documentation if necessary.
5. Submit a pull request with a clear description of the changes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
