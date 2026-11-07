import ast
from typing import Iterator

import pytest

from code_analyser import (check_class_case,
                           check_function_case,
                           check_argument_case,
                           check_variable_case,
                           check_mutable_defaults, FunctionVisitor)

# Helper
def make_nodes(source: str) -> Iterator[ast.AST]:
    return ast.walk(ast.parse(source))


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("class MyClass: pass", [], id="valid-class-name"),
        pytest.param("class myClass: pass", [("myClass", 1)], id="lowercase-first-letter"),
        pytest.param("class my_class: pass", [("my_class", 1)], id="snake-case"),
        pytest.param("class My_Class: pass", [("My_Class", 1)], id="underscore-in-name"),
        pytest.param("class MyClass123: pass", [], id="class-name-with-numbers"),
        pytest.param("class A: pass", [], id="single-letter-name"),
        pytest.param("class myclass: pass", [("myclass", 1)], id="all-lowercase"),
        pytest.param("x = 10", [], id="no-class"),
        pytest.param("x = 10\nclass bad_class: pass", [("bad_class", 2)], id="class-second-line"),
        pytest.param("class Bad_Class: pass\nclass another_class: pass", [("Bad_Class", 1), ("another_class", 2)], id="multiple-invalid-classes")
    ]
)
def test_s008_class_naming(source: str, expected: list[tuple[str, int]]) -> None:
    assert check_class_case(make_nodes(source)) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("def my_function(): pass", [], id="valid-snake-case"),
        pytest.param("def myFunction(): pass", [("myFunction", 1)], id="camel-case"),
        pytest.param("def MyFunction(): pass", [("MyFunction", 1)], id="pascal-case"),
        pytest.param("def MY_FUNCTION(): pass", [("MY_FUNCTION", 1)], id="uppercase-name"),
        pytest.param("def myfunction(): pass", [], id="all-lowercase"),
        pytest.param("def function123(): pass", [], id="function-with-numbers"),
        pytest.param("def _my_function(): pass", [], id="leading-underscore"),
        pytest.param("async def my_function(): pass", [], id="valid-async-function"),
        pytest.param("async def myFunction(): pass", [("myFunction", 1)], id="invalid-async-function"),
        pytest.param("x = 10", [], id="no-function"),
        pytest.param("x = 10\ndef MyFunction(): pass", [("MyFunction", 2)], id="function-second-line"),
        pytest.param("def BadFunction(): pass\ndef anotherFunction(): pass", [("BadFunction", 1), ("anotherFunction", 2)], id="multiple-invalid-functions")
    ]
)
def test_s009_function_naming(source: str, expected: list[tuple[str, int]]) -> None:
    assert check_function_case(make_nodes(source)) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("def foo(my_arg): pass", [], id="valid-snake-case"),
        pytest.param("def foo(myArg): pass", [("myArg", 1)], id="camel-case"),
        pytest.param("def foo(MyArg): pass", [("MyArg", 1)], id="pascal-case"),
        pytest.param("def foo(MY_ARG): pass", [("MY_ARG", 1)], id="uppercase-argument"),
        pytest.param("def foo(arg123): pass", [], id="argument-with-numbers"),
        pytest.param("def foo(_my_arg): pass", [], id="leading-underscore"),
        pytest.param("def foo(first, second): pass", [], id="multiple-valid-arguments"),
        pytest.param("def foo(firstArg, secondArg): pass", [("firstArg", 1), ("secondArg", 1)], id="multiple-invalid-arguments"),
        pytest.param("def foo(argOne, arg_two): pass", [("argOne", 1)], id="mixed-valid-invalid-arguments"),
        pytest.param("def foo(argOne=10): pass", [("argOne", 1)], id="default-argument"),
        pytest.param("def foo(*myArgs): pass", [("myArgs", 1)], id="varargs"),
        pytest.param("def foo(**myKwargs): pass", [("myKwargs", 1)], id="keyword-arguments"),
        pytest.param("def foo(myArg, /): pass", [("myArg", 1)], id="positional-only-argument"),
        pytest.param("def foo(*, myArg): pass", [("myArg", 1)], id="keyword-only-argument"),
        pytest.param("async def foo(myArg): pass", [("myArg", 1)], id="async-function"),
        pytest.param("x = 10\ndef foo(myArg): pass", [("myArg", 2)], id="argument-second-line"),
        pytest.param("x = 10", [], id="no-function")
    ]
)
def test_s010_argument_naming(source: str, expected: list[tuple[str, int]]) -> None:
    assert check_argument_case(make_nodes(source)) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("def foo():\n    my_var = 10", [], id="valid-snake-case"),
        pytest.param("def foo():\n    myVar = 10", [("myVar", 2)], id="camel-case"),
        pytest.param("def foo():\n    MyVar = 10", [("MyVar", 2)], id="pascal-case"),
        pytest.param("def foo():\n    MY_VAR = 10", [("MY_VAR", 2)], id="uppercase-variable"),
        pytest.param("def foo():\n    firstVar = 1\n    secondVar = 2", [("firstVar", 2), ("secondVar", 3)], id="multiple-invalid-variables"),
        pytest.param("def foo():\n    good_var = 1\n    badVar = 2", [("badVar", 3)], id="mixed-valid-invalid-variables"),
        pytest.param("myVar = 10", [], id="module-level-variable"),
        pytest.param("def foo():\n    myVar: int = 10", [("myVar", 2)], id="annotated-assignment"),
        pytest.param("def foo():\n    myVar += 1", [("myVar", 2)], id="augmented-assignment"),
        pytest.param("def foo():\n    firstVar, secondVar = 1, 2", [("firstVar", 2), ("secondVar", 2)], id="tuple-unpacking"),
        pytest.param("def foo():\n    myVar = 10\n    myVar += 1", [("myVar", 2), ("myVar", 3)], id="repeated-assignment"),
        pytest.param("class MyClass:\n    badVar = 10", [], id="class-level-variable"),
        pytest.param("class MyClass:\n    def foo(self):\n        badVar = 10", [("badVar", 3)], id="variable-inside-method"),
        pytest.param("async def foo():\n    badVar = 10", [("badVar", 2)], id="async-function"),
        pytest.param("x = 10", [], id="no-function")
    ]
)
def test_s011_variable_naming(source: str, expected: list[tuple[str, int]]) -> None:
    visitor = FunctionVisitor()
    visitor.visit(ast.parse(source))
    assert check_variable_case(visitor.assignments) == expected


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param("def foo(items=[]): pass", [1], id="list-default"),
        pytest.param("def foo(data={}): pass", [1], id="dict-default"),
        pytest.param("def foo(values=set()): pass", [1], id="set-default"),
        pytest.param("def foo(items=list()): pass", [1], id="list-constructor"),
        pytest.param("def foo(data=dict()): pass", [1], id="dict-constructor"),
        pytest.param("def foo(values={1, 2}): pass", [1], id="set-literal"),
        pytest.param("def foo(value=10): pass", [], id="integer-default"),
        pytest.param('def foo(name="hello"): pass', [], id="string-default"),
        pytest.param("def foo(items=()): pass", [], id="tuple-default"),
        pytest.param("def foo(items=None): pass", [], id="none-default"),
        pytest.param("def foo(items): pass", [], id="no-default"),
        pytest.param("def foo(items=[], data={}): pass", [1], id="multiple-mutable-defaults"),
        pytest.param("def foo(*, items=[]): pass", [1], id="keyword-only-mutable-default"),
        pytest.param("async def foo(items=[]): pass", [1], id="async-function"),
        pytest.param("x = 10\ndef foo(items=[]): pass", [2], id="function-second-line"),
        pytest.param("def foo(items=[]): pass\ndef bar(data={}): pass", [1, 2], id="multiple-functions"),
        pytest.param("x = 10", [], id="no-function")
    ]
)
def test_s012_mutable_defaults(source: str, expected: list[int]) -> None:
    assert check_mutable_defaults(make_nodes(source)) == expected