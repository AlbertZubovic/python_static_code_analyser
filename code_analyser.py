import logging
import sys

from argparse import ArgumentParser
from typing import Final

ERROR_FORMAT: Final = "Line {line}: {code} {message}"

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")


def main() -> None:
    """Parse command-line arguments and run the code analyser."""

    parser = ArgumentParser(description="Check for code violations in the file provided.")
    parser.add_argument("file_path")
    args = parser.parse_args()
    filepath = args.file_path

    check_file(filepath)


def check_file(path: str) -> None:
    """Check a file for code style violations.

    Args:
        path: Path to the file to analyse.
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            logging.info("Successfully opened file: %s", path)
            for line_no, line in enumerate(f, start=1):
                if len(line.rstrip("\n\r")) > 79:
                    report_error(line_no, "S001", "Too long")
                    logging.debug("Line %d exceeds maximum length: %d characters", line_no, len(line.rstrip("\r\n")))


    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Permission denied: {path}", file=sys.stderr)
        sys.exit(1)


def report_error(line_no: int, code: str, message: str) -> None:
    """Print a formatted code style violation."""
    print(ERROR_FORMAT.format(line=line_no, code=code, message=message))


if __name__ == "__main__":
    main()