import io
import pytest
import tokenize

from code_analyser import (check_semicolon,
                           check_inline_comment_spacing,
                           check_todo_comment)


# Helper
def make_tokens(source: str) -> list[tokenize.TokenInfo]:
    return list(tokenize.generate_tokens(io.StringIO(source).readline))


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("x = 10;", [1], id="trailing-semicolon"),
        pytest.param("x = 10", [], id="no-semicolon"),
        pytest.param("x = 10; y = 20", [], id="multiple-statements"),
        pytest.param("x = 10; # comment", [1], id="semicolon-before-comment"),
        pytest.param('x = ";"', [], id="semicolon-in-string"),
        pytest.param("# x = 10;", [], id="semicolon-in-comment"),
        pytest.param("x = 10;\ny = 20", [1], id="semicolon-first-line"),
        pytest.param("x = 10\ny = 20;", [2], id="semicolon-second-line"),
        pytest.param("x = 10;\ny = 20;", [1, 2], id="multiple-trailing-semicolons")
    ]
)
def test_s003_semicolon(source: str, expected: list[int]) -> None:
    assert check_semicolon(make_tokens(source)) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("x = 10  # comment", [], id="two-spaces"),
        pytest.param("x = 10 # comment", [1], id="one-space"),
        pytest.param("x = 10# comment", [1], id="no-spaces"),
        pytest.param("x = 10   # comment", [], id="three-spaces"),
        pytest.param("# comment", [], id="full-line-comment"),
        pytest.param("    # comment", [], id="indented-full-line-comment"),
        pytest.param('x = "# comment"', [], id="hash-in-string"),
        pytest.param("x = 10 # comment\ny = 20", [1], id="first-line"),
        pytest.param("x = 10\ny = 20 # comment", [2], id="second-line"),
        pytest.param("x = 10 # comment\ny = 20 # comment", [1, 2], id="multiple-inline-comments")
    ]
)
def test_s004_inline_comment_spacing(source: str, expected: list[int]) -> None:
    assert check_inline_comment_spacing(make_tokens(source)) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("# TODO: fix", [1], id="todo-comment"),
        pytest.param("# todo: fix", [1], id="lowercase-todo"),
        pytest.param("# Todo: fix", [1], id="mixed-case-todo"),
        pytest.param("x = 10  # TODO: fix", [1], id="inline-todo"),
        pytest.param("# normal comment", [], id="no-todo"),
        pytest.param('x = "# TODO"', [], id="todo-in-string"),
        pytest.param("x = 10\n# TODO: fix", [2], id="todo-second-line"),
        pytest.param("# TODO: first\nx = 10\n# TODO: second", [1, 3], id="multiple-todo-comments"),
        pytest.param("# TODO: fix\n# normal comment", [1], id="todo-and-normal-comment"),
        pytest.param("x = 10", [], id="no-comment")
    ]
)
def test_s005_todo_comment(source: str, expected: list[int]) -> None:
    assert check_todo_comment(make_tokens(source)) == expected
