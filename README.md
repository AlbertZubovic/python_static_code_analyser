# Python Static Code Analyzer
A command-line static code analyser that checks individual Python files or directories
for common PEP 8 style violations and Python coding issues.

## Features
- Accepts a single Python file or a directory containing Python files.
- Detects 12 style violations (S001-S012).
- Reports violations with their file path, line number, error code and description.

## Supported Style Checks
The Python files are analysed based on the style violations outlined below:

| Code | Description                                                   |
|------|---------------------------------------------------------------|
| S001 | Line exceeds 79 characters                                    |
| S002 | Indentation is not a multiple of four spaces                  |
| S003 | Unnecessary semicolon                                         |
| S004 | Fewer than two spaces before an inline comment                |
| S005 | TODO found in a comment                                       |
| S006 | More than two consecutive blank lines before a code statement |
| S007 | Too many spaces after `def` or `class`                           |
| S008 | Class name should use `CapWords` convention                     |
| S009 | Function name should use `snake_case`                           |
| S010 | Argument name should use `snake_case`                           |
| S011 | Variable name should use `snake_case`                           |
| S012 | Mutable default argument                                      |

## Implementation
The analyser uses source-level checks, Python's `tokenize` module and the abstract
syntax tree (`ast`) module to detect formatting violations, naming convention issues
and mutable default arguments.

## Project Structure
```text
python_static_code_analyser/
├── tests/
│   ├── test_ast_checks.py
│   ├── test_integration.py
│   ├── test_line_checks.py
│   └── test_token_checks.py
├── .gitignore
├── code_analyser.py
├── LICENSE
└── README.md
```

## Requirements
- Python 3.14 (tested; compatibility with earlier versions not verified)
- No third-party dependencies required to run the analyser

## Installation
```bash
git clone https://github.com/AlbertZubovic/python_static_code_analyser.git
cd python_static_code_analyser
```

## Usage
To analyse a Python file:

```bash
py -m code_analyser example.py
```

To analyse a directory of Python files:

```bash
py -m code_analyser example/
```

### Example Output
```bash
example.py: Line 1: S003 Unnecessary semicolon after a statement
example.py: Line 2: S009 Function name 'BadFunction' should be written in snake_case
example.py: Line 3: S005 TODO found
example.py: Line 3: S011 Variable 'badVar' should be written in snake_case
```

## Testing
The project includes unit tests for individual style checks
and integration tests for file analysis.

Install pytest:

```bash
py -m pip install pytest
```

Run the test suite:

```bash
py -m pytest -v
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.