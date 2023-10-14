import os

import pytest

from slyp.checkers import _clear_errors, check_file


@pytest.fixture(autouse=True)
def _auto_clear_errors():
    _clear_errors()


def test_check_passes_on_example_file(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
x = "foo bar"

foo(x="foo bar")
foo(
    x=(
        "foo "
        "bar"
    )
)

y = {
    "foo": "bar",
}
y = {
    "foo": ("bar"
    "baz"),
}

z = (
    "alpha",
    "beta",
    "gamma",
)
z = [
    "alpha",
    "beta",
    "gamma",
]
z = {
    "alpha",
    "beta",
    "gamma",
}
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is True


def test_check_captures_e100(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
x = "foo" "bar"
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is False

    assert "foo.py:1: unnecessary string concat (E100)" in capsys.readouterr().out


def test_check_captures_e101(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo(x="foo"
"bar")
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is False

    assert (
        "foo.py:1: unparenthesized multiline string concat in keyword arg (E101)"
        in capsys.readouterr().out
    )


def test_check_captures_e102(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo = {
    "x": "foo"
"bar"
}
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: unparenthesized multiline string concat in dict value (E102)"
        in capsys.readouterr().out
    )


def test_check_captures_e103(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo = (
    "alpha",
    "beta"
    "gamma",
)
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is False

    assert (
        "foo.py:3: unparenthesized multiline string concat in collection type (E103)"
        in capsys.readouterr().out
    )


def test_check_captures_w200(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz()
    elif qux():
        return quux()
    else:
        return baz()
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: two AST branches have identical contents (W200)"
        in capsys.readouterr().out
    )


def test_can_disable_code_with_comment(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():  # slyp: disable=W200
        return baz()
    elif qux():
        return quux()
    else:
        return baz()
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set())
    assert res is True

    assert (
        "two AST branches have identical contents (W200)" not in capsys.readouterr().out
    )
