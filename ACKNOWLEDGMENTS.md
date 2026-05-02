# Acknowledgments and Third-Party Licenses

This project incorporates components from several open-source libraries. We are grateful to the maintainers and contributors of these projects.

## Dependencies

### tree-sitter (py-tree-sitter)
- **License**: MIT
- **Project URL**: [https://github.com/tree-sitter/py-tree-sitter](https://github.com/tree-sitter/py-tree-sitter)
- **Use Case**: Used for AST-based multi-language syntax verification.

### rope
- **License**: LGPLv3
- **Project URL**: [https://github.com/python-rope/rope](https://github.com/python-rope/rope)
- **Use Case**: Used for Python refactoring (rename).
- **Compliance Note**: This project uses `rope` as an external library and does not modify its source code. Our use of `rope` is consistent with LGPLv3 requirements.

### pytest
- **License**: MIT
- **Project URL**: [https://github.com/pytest-dev/pytest](https://github.com/pytest-dev/pytest)
- **Use Case**: Used for unit and integration testing.

---

## MIT License (for tree-sitter and pytest components)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
