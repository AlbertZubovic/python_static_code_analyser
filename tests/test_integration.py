from code_analyser import check_file


def test_multiple_violations(tmp_path, capsys) -> None:
    file = tmp_path / "example.py"
    file.write_text(
        "x = 10;\n"
        "def BadFunction():\n"
        "    badVar = 10  # TODO: fix\n",
        encoding="utf-8",
    )

    check_file(str(file))

    output = capsys.readouterr().out

    expected = (
        f"{file}: Line 1: S003 Unnecessary semicolon after a statement\n"
        f"{file}: Line 2: S009 Function name 'BadFunction' should be written in snake_case\n"
        f"{file}: Line 3: S005 TODO found\n"
        f"{file}: Line 3: S011 Variable 'badVar' should be written in snake_case\n"
    )

    assert output == expected


def test_no_violations(tmp_path, capsys) -> None:
    file = tmp_path / "example.py"
    file.write_text(
        "def my_function():\n"
        "    my_var = 10\n",
        encoding="utf-8",
    )

    check_file(str(file))

    output = capsys.readouterr().out

    assert output == ""