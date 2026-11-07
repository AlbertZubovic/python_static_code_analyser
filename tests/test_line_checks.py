import pytest

from code_analyser import (check_line_length,
                           check_blank_line,
                           check_indentation,
                           check_construction_spacing)


@pytest.mark.parametrize(
    "line, expected",
    [
        pytest.param("x = 10", False, id="short-line"),
        pytest.param("a" * 79, False, id="at-line"),
        pytest.param("a" * 80, True, id="over-limit"),
        pytest.param("", False, id="empty-line"),
        pytest.param("a" * 79 + "\n", False, id="at-limit-with-newline"),
        pytest.param("a" * 80 + "\n", True, id="over-limit-with-newline")
    ]
)
def test_s001_line_length(line: str, expected: bool) -> None:
    assert check_line_length(line) == expected


@pytest.mark.parametrize(
    "line, expected",
    [
        pytest.param("    x = 10", False, id="four-spaces"),
        pytest.param("   x = 10", True, id="three-spaces"),
        pytest.param("        x = 10", False, id="eight-spaces"),
        pytest.param("     x = 10", True, id="five-spaces"),
        pytest.param("x = 10", False, id="no-indentation")
    ]
)
def test_s002_indentation(line: str, expected: bool) -> None:
    assert check_indentation(line) == expected


@pytest.mark.parametrize(
    "line, blank_count, expected",
    [
        pytest.param("x = 10", 0, False, id="no-blank-lines"),
        pytest.param("x = 10", 1, False, id="one-blank-line"),
        pytest.param("x = 10", 2, False, id="two-blank-lines"),
        pytest.param("x = 10", 3, True, id="three-blank-lines"),
        pytest.param("x = 10", 4, True, id="four-blank-lines"),
        pytest.param("\n", 3, False, id="blank-current-line")
    ]
)
def test_s006_blank_lines(line: str, blank_count: int, expected: bool) -> None:
    assert check_blank_line(line, blank_count) == expected


@pytest.mark.parametrize(
    "line, expected",
    [
        pytest.param("def foo():", None, id="def-one-space"),
        pytest.param("def  foo():", "def", id="def-two-spaces"),
        pytest.param("def   foo():", "def", id="def-three-spaces"),
        pytest.param("class Foo:", None, id="class-one-space"),
        pytest.param("class  Foo:", "class", id="class-two-spaces"),
        pytest.param("class   Foo:", "class", id="class-three-spaces"),
        pytest.param("    def foo():", None, id="indented-def-one-space"),
        pytest.param("    def  foo():", "def", id="indented-def-two-spaces"),
        pytest.param("x = 10", None, id="regular-statement"),
    ]
)
def test_s007_construction_spacing(line: str, expected: bool) -> None:
    assert check_construction_spacing(line) == expected


