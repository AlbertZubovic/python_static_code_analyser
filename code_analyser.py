import logging
import os
import re
import sys

from argparse import ArgumentParser
from typing import Final

ERROR_FORMAT: Final = "{path}: Line {line}: {code} {message}"

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")


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
    """Check a file for code style violations.

    Args:
        path: Path to the file to analyse.
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            logging.info("Successfully opened file: %s", path)
            blank_count = 0
            for line_no, line in enumerate(f, start=1):

                if check_line_length(line):
                    report_error(path, line_no, "S001", "Too long")

                if check_indentation(line):
                    report_error(path, line_no, "S002", "Indentation is not a multiple of four")

                if check_semicolon(line):
                    report_error(path, line_no, "S003", "Unnecessary semicolon after a statement")

                if check_inline_comment_spacing(line):
                    report_error(path, line_no, "S004", "Less than two spaces before inline comments")

                if check_todo_comment(line):
                    report_error(path, line_no, "S005", "TODO found")

                if check_blank_line(line, blank_count):
                    report_error(path, line_no, "S006", "More than two blank lines preceding a code line")

                construction_keyword = check_construction_spacing(line)

                if construction_keyword:
                    report_error(path, line_no, "S007",f"Too many spaces after '{construction_keyword}'")

                invalid_class_name = check_class_case(line)

                if invalid_class_name:
                    report_error(path, line_no, "S008", f"Class name '{invalid_class_name}' should be written in CamelCase")

                invalid_function_name = check_function_case(line)

                if invalid_function_name:
                    report_error(path, line_no, "S009", f"Function name '{invalid_function_name}' should be written in snake_case")


                if not line.strip():
                    blank_count += 1
                else:
                    blank_count = 0


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
    """Returns True if the line exceeds 79 characters."""
    return len(line.rstrip("\n\r")) > 79

def check_indentation(line: str) -> bool:
    """Return True if indentation is not a multiple of four spaces."""
    return (len(line) - len(line.lstrip(" "))) % 4 != 0

def check_semicolon(line: str) -> bool:
    """Return True if the line ends with an unnecessary semicolon."""
    code = line.split("#", 1)[0].strip()

    return code.endswith(";")

def check_inline_comment_spacing(line: str) -> bool:
    """Return True if an inline comment has fewer than two preceding spaces."""
    if "#" not in line:
        return False

    if line.strip().startswith("#"):
        return False

    return not line.split("#", 1)[0].endswith("  ")

def check_todo_comment(line: str) -> bool:
    """Return True if a comment contains TODO, ignoring case."""
    if "#" not in line:
        return False

    return "todo" in line.split("#", 1)[1].lower()

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

def check_class_case(line: str) -> str|None:
    """Return an invalid class name, or None if its naming is valid."""

    definition = re.match(r"class\s+(\w+)", line.lstrip())

    if definition:
        class_name = definition.group(1)
        if not (class_name[0].isupper() and "_" not in class_name):
            return class_name
    return None

def check_function_case(line: str) -> str|None:
   """Return an invalid function name, or None if its naming is valid."""

   definition = re.match(r"(?:async\s+)?def\s+(\w+)", line.lstrip())

   if definition:
       function_name = definition.group(1)
       if any(char.isupper() for char in function_name):
           return function_name
   return None


if __name__ == "__main__":
    main()