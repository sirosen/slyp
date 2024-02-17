import textwrap

import pytest


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


@pytest.mark.parametrize("layers", (1, 2))
def test_paren_fixer_preserves_innermost_under_splatarg(fix_text, layers):
    new_text = fix_text(
        f"""\
        foo(*{'(' * layers}"a b c".split(){')' * layers})
        """,
        expect_changes=layers > 1,
    )
    assert new_text == 'foo(*("a b c".split()))\n'


def test_multiline_always_allowed(fix_text):
    fix_text(
        """\
        a = (
            (
                (1, 2)
            )
        )
        """,
        expect_changes=False,
    )


def test_names_attributes_and_indexing(fix_text):
    new_text = fix_text(
        """\
        a = (x)
        b = (x.y)
        c = (x).y
        d = x["y"]
        e = (x)["y"]
        f = (x["y"])
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = x
        b = x.y
        c = x.y
        d = x["y"]
        e = x["y"]
        f = x["y"]
        """
    )


def test_collection_types(fix_text):
    new_text = fix_text(
        """\
        a = {1: 2}
        b = ({2: 3})
        c = {x: y for x, y in foo()}
        d = ({x: y for x, y in foo()})
        e = [1, 2]
        f = ([3, 4])
        g = [x for x in foo()]
        h = ([x for x in foo()])
        i = {1}
        j = ({2})
        k = {x for x in foo()}
        l = ({x for x in foo()})
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {1: 2}
        b = {2: 3}
        c = {x: y for x, y in foo()}
        d = {x: y for x, y in foo()}
        e = [1, 2]
        f = [3, 4]
        g = [x for x in foo()]
        h = [x for x in foo()]
        i = {1}
        j = {2}
        k = {x for x in foo()}
        l = {x for x in foo()}
        """
    )


def test_operators_and_numerics(fix_text):
    new_text = fix_text(
        """\
        a = ((1 + 2)) * (3.2)
        b = ((~ (1 - 2))) * 3 - 2.2
        c = (((a < b) | 1))
        d = a * b
        e = -d
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = (1 + 2) * (3.2)
        b = (~ (1 - 2)) * 3 - 2.2
        c = ((a < b) | 1)
        d = a * b
        e = -d
        """
    )


def test_ellipsis(fix_text):
    new_text = fix_text(
        """\
        a = ((...))
        b = ...
        """
    )
    assert new_text == "a = ...\nb = ...\n"


def test_string_styles(fix_text):
    # note that the ConcatenatedString node will also be fixed to a single string
    new_text = fix_text(
        """\
        x = "foo"
        a = ("foo")
        b = (("foo " "bar"))
        c = (((f"baz {a}")))
        """
    )
    assert new_text == textwrap.dedent(
        """\
        x = "foo"
        a = "foo"
        b = "foo bar"
        c = f"baz {a}"
        """
    )


def test_lambdas_and_yields_with_many_parens(fix_text):
    new_text = fix_text(
        """\
        a = ((lambda: 1))
        b = (lambda: ((1)))
        c = lambda: (yield)
        d = lambda: ((yield))
        e = lambda: (yield from foo())
        f = lambda: ((yield from foo()))
        g = (lambda: ((yield from foo())))
        h = ((lambda: ((yield from foo()))))
        i = ((((lambda: ((yield from foo()))))))
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = (lambda: 1)
        b = (lambda: (1))
        c = lambda: (yield)
        d = lambda: (yield)
        e = lambda: (yield from foo())
        f = lambda: (yield from foo())
        g = (lambda: (yield from foo()))
        h = (lambda: (yield from foo()))
        i = (lambda: (yield from foo()))
        """
    )


def test_generator_expressions(fix_text):
    new_text = fix_text(
        """\
        a = list(x for x in foo())
        b = foo((x for x in bar()), baz())
        c = foo(((x for x in bar())), baz())
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = list(x for x in foo())
        b = foo((x for x in bar()), baz())
        c = foo((x for x in bar()), baz())
        """
    )


def test_if_expressions(fix_text):
    new_text = fix_text(
        """\
        a = (1 if x else 2) | 3
        b = 1 if x else 2 & a
        c = ((1 if a else 2)) or b
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        a = (1 if x else 2) | 3
        b = 1 if x else 2 & a
        c = (1 if a else 2) or b
        """,
    )


def test_await_safe_use_for_precedence(fix_text):
    new_text = fix_text(
        """\
        a = (await foo() if x else bar())["baz"]
        b = ((await foo() if x else bar()))
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = (await foo() if x else bar())["baz"]
        b = (await foo() if x else bar())
        """
    )


def test_match_with_paren_gets_space_inserted(fix_text):
    new_text = fix_text(
        """\
        match(x):
            case (1, 2):
                pass
            case _:
                pass
        """
    )
    assert new_text == textwrap.dedent(
        """\
        match x:
            case (1, 2):
                pass
            case _:
                pass
        """
    )


def test_with_with_paren_gets_space_inserted(fix_text):
    new_text = fix_text(
        """\
        with(x()):
            pass
        """
    )
    assert new_text == textwrap.dedent(
        """\
        with x():
            pass
        """
    )


def test_if_with_paren_gets_space_inserted(fix_text):
    new_text = fix_text(
        """\
        if(x()):
            pass
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if x():
            pass
        """
    )


def test_import_from_gets_space_inserted(fix_text):
    new_text = fix_text(
        """\
        from foo import(bar, baz)
        """
    )
    assert new_text == "from foo import bar, baz\n"


def test_unary_op_preserves_parens(fix_text):
    fix_text(
        """\
        foo(~(bar.baz()))
        """,
        expect_changes=False,
    )
