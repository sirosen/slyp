def test_paren_fixer_no_op(capsys, fix_text):
    fix_text(
        "x = 1\n",
        expect_changes=False,
        verbose=True,
        filename="foo.py",
    )
    assert "slyp: no changes to foo.py" in capsys.readouterr().out


def test_paren_fixer_is_no_op_on_needed_parens(fix_text):
    fix_text(
        """\
        a = [(1,), (2, 3)]
        b = foo((x % 2 for x in range(10)), bar)
        c = (1+2)*3
        d = -1 * (-(1+2))
        e = (foo() if x else bar())["baz"]
        f = (await foo())["bar"]
        g = (1).bit_length()
        h = (2.2).is_integer()
        i = (x is y) in truefalsecontainer
        j = lambda: 1, 2
        k = (lambda: 1), 2
        l = (lambda: 1)(2)
        """,
        expect_changes=False,
    )


def test_fix_unnecessary_double_paren_tuple(capsys, fix_text):
    new_text = fix_text(
        "a = ((1, 2))\n",
        verbose=True,
        filename="foo.py",
    )

    assert "slyp: fixing foo.py" in capsys.readouterr().out
    assert new_text == "a = (1, 2)\n"


def test_fix_unnecessary_many_paren_string(fix_text):
    new_text = fix_text('a = ((((((("foo")))))))\n')
    assert new_text == 'a = "foo"\n'


def test_paren_fixer_preserves_innermost_under_splatarg(fix_text):
    new_text = fix_text(
        """\
        foo(*(("a b c".split())))
        """
    )
    assert new_text == 'foo(*("a b c".split()))\n'
