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

Note: Some tests for Go and Java require the respective Language Servers (`gopls`, `jdtls`) to be installed on your system.

## Pull Request Process

1. Create a new branch for your feature or bugfix.
2. Ensure all tests pass locally.
3. Add new tests if you are adding functionality or fixing a bug.
4. Update the documentation if necessary.
5. Submit a pull request with a clear description of the changes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
