import os

import pytest

from slyp.checkers import _clear_errors, check_file


@pytest.fixture(autouse=True)
def _auto_clear_errors():
    _clear_errors()


def test_check_passes_on_example_file(tmpdir):
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
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is True


def test_check_captures_e100(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
x = "foo" "bar"
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert "foo.py:1: unnecessary string concat (E100)" in capsys.readouterr().out


def test_check_captures_w101(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo(x="foo"
"bar")
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:1: unparenthesized multiline string concat in keyword arg (W101)"
        in capsys.readouterr().out
    )


def test_check_captures_w102(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo = {
    "x": "foo"
"bar"
}
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: unparenthesized multiline string concat in dict value (W102)"
        in capsys.readouterr().out
    )


def test_check_captures_w103(tmpdir, capsys):
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
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:3: unparenthesized multiline string concat in collection type (W103)"
        in capsys.readouterr().out
    )


def test_check_w103_ignores_solo_strings(tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo = [
    "alpha"
    "beta"
]
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is True


def test_check_captures_w200(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz(quux("snork"))
    else:
        return baz(quux("snork"))
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: two AST branches have identical contents (W200)"
        in capsys.readouterr().out
    )


def test_check_captures_w201(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz()
    else:
        return baz()
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: two AST branches have identical trivial contents (W201)"
        in capsys.readouterr().out
    )


def test_check_captures_w202(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz("snork", flip="flop")
    elif qux():
        return quux()
    else:
        return baz("snork", flip="flop")
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: two non-adjacent AST branches have identical contents (W202)"
        in capsys.readouterr().out
    )


def test_check_captures_w203(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz("snork")
    elif qux():
        return quux()
    else:
        return baz("snork")
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:2: two non-adjacent AST branches have identical trivial contents (W203)"
        in capsys.readouterr().out
    )


def test_can_disable_code_with_comment(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    x = "a " "b"  # slyp: disable=E100
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is True

    assert "(E100)" not in capsys.readouterr().out


def test_can_disable_code_via_category_disable(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
def foo():
    if bar():
        return baz("snork")
    elif qux():
        return quux()
    else:
        return baz("snork")
"""
    )
    res = check_file(
        "foo.py", verbose=False, disabled_codes=set("W"), enabled_codes=set()
    )
    assert res is True

    assert "(W203)" not in capsys.readouterr().out


def test_check_captures_e110(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
if foo is None:
    return foo
"""
    )
    res = check_file("foo.py", verbose=False, disabled_codes=set(), enabled_codes=set())
    assert res is False

    assert (
        "foo.py:1: returning a variable checked as None, "
        "rather than returning None (E110)"
    ) in capsys.readouterr().out
