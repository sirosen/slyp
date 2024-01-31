import os

from slyp.fixers import fix_file


def test_fixer_no_op(capsys, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
x = 1
"""
    )
    res = fix_file("foo.py", verbose=True)

    assert res
    assert "slyp: no changes to foo.py" in capsys.readouterr().out
    assert tmpdir.join("foo.py").read() == "x = 1\n"


def test_fixer_is_no_op_on_needed_parens(tmpdir):
    os.chdir(tmpdir)
    body = """\
a = [(1,), (2, 3)]
b = foo((x % 2 for x in range(10)), bar)
c = (1+2)*3
d = -1 * (-(1+2))
e = (foo() if x else bar())["baz"]
f = (await foo())["bar"]
g = (1).bit_length()
h = (2.2).is_integer()
i = (x is y) in truefalsecontainer
"""
    tmpdir.join("foo.py").write(body)
    res = fix_file("foo.py", verbose=True)
    assert res
    assert tmpdir.join("foo.py").read() == body


def test_fix_unnecessary_double_paren_tuple(capsys, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
a = ((1, 2))
"""
    )
    res = fix_file("foo.py", verbose=True)

    assert not res
    assert "slyp: fixing foo.py" in capsys.readouterr().out
    assert tmpdir.join("foo.py").read() == "a = (1, 2)\n"


def test_fix_unnecessary_many_paren_string(capsys, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
a = ((((((("foo")))))))
"""
    )
    res = fix_file("foo.py", verbose=True)

    assert not res
    assert "slyp: fixing foo.py" in capsys.readouterr().out
    assert tmpdir.join("foo.py").read() == 'a = "foo"\n'


def test_paren_fixer_preserves_innermost_under_splatarg(capsys, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
foo(*(("a b c".split())))
"""
    )
    res = fix_file("foo.py", verbose=False)

    assert not res
    assert "slyp: fixing foo.py" in capsys.readouterr().out
    assert (
        tmpdir.join("foo.py").read()
        == """\
foo(*("a b c".split()))
"""
    )
