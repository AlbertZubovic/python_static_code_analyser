"""A static code analyser for Python style violations S001-S012.

Check source formatting, naming conventions, local variables
and mutable default arguments.
"""

import ast
import io
import logging
import os
import sys
import tokenize

from argparse import ArgumentParser
from collections.abc import Sequence
from typing import Final, Iterator, Iterable

ERROR_FORMAT: Final = "{path}: Line {line}: {code} {message}"

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")


class FunctionVisitor(ast.NodeVisitor):
    """Collect local variable assignments while excluding class-body assignments."""

    def __init__(self):
        self.function_depth = 0
        self.class_depth = 0
        self.assignments: list[tuple[str, int]] = []


    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function scope while visiting its contents."""

        self.function_depth += 1

        # A function introduces a new scope, even when defined inside a class.
        previous_class_depth = self.class_depth
        self.class_depth = 0

        try:
            self.generic_visit(node)
        finally:
            self.function_depth -= 1
            self.class_depth = previous_class_depth

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.function_depth > 0 and self.class_depth == 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.assignments.append((target.id, target.lineno))

                elif isinstance(target, ast.Tuple):
                    for element in target.elts:
                        if isinstance(element, ast.Name):
                            self.assignments.append((element.id, element.lineno))

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self.function_depth > 0 and self.class_depth == 0:
            if isinstance(node.target, ast.Name):
                self.assignments.append((node.target.id, node.target.lineno))

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.function_depth > 0 and self.class_depth == 0:
            if isinstance(node.target, ast.Name):
                self.assignments.append((node.target.id, node.target.lineno))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self.class_depth -= 1


def main() -> None:
    """Parse command-line arguments and run the code analyser."""

    parser = ArgumentParser(description="Check for code violations in a file or directory provided.")
    parser.add_argument("file_path", type=str)
    args = parser.parse_args()
    filepath: str = args.file_path

    if filepath.endswith(".py"):
        check_file(filepath)
    elif os.path.isdir(filepath):
        file_paths: list[str] = []

        for root, _, files in os.walk(filepath):
                for file in files:
                    if file.endswith(".py"):
                        file_paths.append(os.path.join(root, file))

        for path in sorted(file_paths):
            check_file(path)


def check_file(path: str) -> None:
    """Analyse a file for S001-S012 style violations.

    Use line-based checks for formatting, token-based checks for
    comments and semicolons, and AST-based checks for naming and
    mutable default arguments.

    Collect and sort violations before reporting them.
    """

    try:

        violations: list[tuple[str, int, str, str]] = []

        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

            logging.info("Successfully opened file: %s", path)

            # Check formatting rules using the original source lines.
            blank_count = 0
            for line_no, line in enumerate(source.splitlines(keepends=True), start=1):

                if check_line_length(line):
                    violations.append((path , line_no, "S001", "Too long"))

                if check_indentation(line):
                    violations.append((path , line_no, "S002", "Indentation is not a multiple of four"))

                if check_blank_line(line, blank_count):
                    violations.append((path , line_no, "S006", "More than two blank lines preceding a code line"))

                construction_keyword = check_construction_spacing(line)

                if construction_keyword:
                    violations.append((path , line_no, "S007", f"Too many spaces after '{construction_keyword}'"))


                if not line.strip():
                    blank_count += 1
                else:
                    blank_count = 0


        tree = ast.parse(source)
        visitor = FunctionVisitor()
        visitor.visit(tree)
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

        # Check comments and end of statement rules using tokenizer.
        for line_no in check_semicolon(tokens):
            violations.append((path, line_no, "S003", "Unnecessary semicolon after a statement"))

        for line_no in check_inline_comment_spacing(tokens):
            violations.append((path, line_no, "S004", "Less than two spaces before inline comments"))

        for line_no in check_todo_comment(tokens):
            violations.append((path, line_no, "S005", "TODO found"))

        # Check naming and default-argument rules using the AST
        invalid_class_names = check_class_case(ast.walk(tree))
        for class_name, line_no in invalid_class_names:
            violations.append((path, line_no, "S008", f"Class name '{class_name}' should be written in CamelCase"))

        invalid_function_names = check_function_case(ast.walk(tree))
        for function_name, line_no in invalid_function_names:
            violations.append((path, line_no, "S009", f"Function name '{function_name}' should be written in snake_case"))

        invalid_arguments = check_argument_case(ast.walk(tree))
        for arg_name, line_no in invalid_arguments:
            violations.append((path, line_no, "S010", f"Argument name '{arg_name}' should be written in snake_case"))

        invalid_variables = check_variable_case(visitor.assignments)
        for variable_name, line_no in invalid_variables:
            violations.append((path, line_no, "S011", f"Variable '{variable_name}' should be written in snake_case"))

        for line_no in check_mutable_defaults(ast.walk(tree)):
            violations.append((path, line_no, "S012", f"The default argument value is mutable"))


        violations.sort(key=lambda x: (x[1], x[2]))

        for violation in violations:
            report_error(*violation)

    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Permission denied: {path}", file=sys.stderr)
        sys.exit(1)


def report_error(path: str, line_no: int, code: str, message: str) -> None:
    """Print a formatted code style violation."""
    print(ERROR_FORMAT.format(path=path, line=line_no, code=code, message=message))


# Static code checkers

def check_line_length(line: str) -> bool:
    """Return True if the line exceeds 79 characters."""
    return len(line.rstrip("\n\r")) > 79

def check_indentation(line: str) -> bool:
    """Return True if indentation is not a multiple of four spaces."""
    return (len(line) - len(line.lstrip(" "))) % 4 != 0

def check_semicolon(tokens: Sequence[tokenize.TokenInfo]) -> list[int]:
    """Return line numbers of statements that end with an unnecessary semicolon."""

    semicolon_lines = []
    for i, token in enumerate(tokens):
        if token.type == tokenize.OP and token.string == ";":
            next_token = tokens[i + 1]

            if next_token.type in (tokenize.NEWLINE, tokenize.COMMENT):
                semicolon_lines.append(token.start[0])
    return semicolon_lines

def check_inline_comment_spacing(tokens: Iterable[tokenize.TokenInfo]) -> list[int]:
    """Return line numbers of comments with fewer than two preceding spaces."""

    invalid_comment_lines = []
    for token in tokens:
        if token.type == tokenize.COMMENT:
            comment_column = token.start[1]
            before_comment = token.line[:comment_column]
            if before_comment.strip() and not before_comment.endswith("  "):
                invalid_comment_lines.append(token.start[0])
    return invalid_comment_lines

def check_todo_comment(tokens: Iterable[tokenize.TokenInfo]) -> list[int]:
    """Return line numbers of comments containing TODO."""

    todo_lines = []
    for token in tokens:
        if token.type == tokenize.COMMENT:
            if "todo" in token.string.lower():
                todo_lines.append(token.start[0])
    return todo_lines

def check_blank_line(line: str, blank_count: int) -> bool:
    """Return True if a non-empty line follows more than two blank lines."""
    return blank_count > 2 and bool(line.strip())

def check_construction_spacing(line: str) -> str|None:
    """Return the keyword with excessive spacing, or None if valid."""
    line = line.lstrip()

    if line.startswith("def "):
        line = line[3:]
        if (len(line) - len(line.lstrip())) > 1:
            return "def"
    elif line.startswith("class "):
        line = line[5:]
        if (len(line) - len(line.lstrip())) > 1:
            return "class"
    return None

def check_class_case(nodes: Iterator[ast.AST]) -> list[tuple[str, int]]:
    """Return invalid class names and their line numbers."""
    invalid_class_names = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            line_no = node.lineno
            if not (class_name[0].isupper() and "_" not in class_name):
                invalid_class_names.append((class_name, line_no))
    return invalid_class_names

def check_function_case(nodes: Iterator[ast.AST]) -> list[tuple[str, int]]:
    """Return invalid function names and their line numbers."""
    invalid_function_names = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_name = node.name
            line_no = node.lineno
            if any(char.isupper() for char in function_name):
                invalid_function_names.append((function_name, line_no))
    return invalid_function_names

def check_argument_case(nodes: Iterator[ast.AST]) -> list[tuple[str, int]]:
    """Returns invalid arguments and their line numbers."""

    invalid_arguments = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in (node.args.posonlyargs
                        + node.args.args
                        + node.args.kwonlyargs
                        + ([node.args.vararg] if node.args.vararg else [])
                        + ([node.args.kwarg] if node.args.kwarg else [])):
                arg_name = arg.arg
                line_no = arg.lineno
                if any(char.isupper() for char in arg_name):
                    invalid_arguments.append((arg_name, line_no))
    return invalid_arguments

def check_variable_case(variables: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Return invalid local variable names and their line numbers."""

    invalid_variables = []
    for variable_name, line_no in variables:
        if any(char.isupper() for char in variable_name):
            invalid_variables.append((variable_name, line_no))
    return invalid_variables

def check_mutable_defaults(nodes: Iterator[ast.AST]) -> list[int]:
    """Return mutable default line numbers."""
    invalid_defaults = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            # Report only once per function, even with multiple mutable defaults.
            for default in node.args.defaults + node.args.kw_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    invalid_defaults.append(node.lineno)
                    break
                elif isinstance(default, ast.Call) and isinstance(default.func, ast.Name) and default.func.id in ("set", "list", "dict"):
                    invalid_defaults.append(node.lineno)
                    break
    return invalid_defaults


if __name__ == "__main__":
    main()