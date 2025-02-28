import pytest


@pytest.mark.parametrize("expr", ("if", "try", "ifexpr", "ifexpr-in-if-test"))
def test_check_captures_w200(check_text, expr):
    if expr == "if":
        content = """\
            def foo():
                if bar():
                    return baz(quux("snork"))
                else:
                    return baz(quux("snork"))
        """
    elif expr == "try":
        content = """\
            def foo():
                try:
                    return baz(quux("snork"))
                except:
                    return baz(quux("snork"))
        """
    elif expr == "ifexpr":
        content = """\
            def foo():
                return baz(quux("snork")) if buzz() else baz(quux("snork"))
        """
    elif expr == "ifexpr-in-if-test":
        content = """\
            def foo():
                if baz(quux("snork")) if buzz() else baz(quux("snork")):
                    return 1
                return 0
        """
    else:
        raise NotImplementedError

    res = check_text(content, filename="foo.py")

    assert not res.success
    assert (
        "foo.py:2: two AST branches have identical contents (W200)"
        in res.message_strings
    )


def test_check_captures_w201(check_text):
    res = check_text(
        """\
        def foo():
            if bar():
                return baz()
            else:
                return baz()
        """,
        filename="foo.py",
    )

    assert not res.success
    assert (
        "foo.py:2: two AST branches have identical trivial contents (W201)"
        in res.message_strings
    )


def test_check_captures_w202(check_text):
    res = check_text(
        """\
        def foo():
            if bar():
                return baz("snork", flip="flop")
            elif qux():
                return quux()
            else:
                return baz("snork", flip="flop")
        """,
        filename="foo.py",
    )

    assert not res.success
    assert (
        "foo.py:2: two non-adjacent AST branches have identical contents (W202)"
        in res.message_strings
    )


def test_check_captures_w203(check_text):
    res = check_text(
        """\
        def foo():
            if bar():
                return baz("snork")
            elif qux():
                return quux()
            else:
                return baz("snork")
        """,
        filename="foo.py",
    )

    assert not res.success
    assert (
        "foo.py:2: two non-adjacent AST branches have identical trivial contents (W203)"
        in res.message_strings
    )


def test_captures_nested_w200s(check_text):
    res = check_text(
        """\
        def foo():
            if bar():
                return baz(quux("snork"))
            elif bar2():
                return baz(quux("snork"))
            else:
                try:
                    return baz(snork("quux"))
                except:
                    return baz(snork("quux"))
        """,
        filename="foo.py",
    )

    assert not res.success
    assert (
        "foo.py:2: two AST branches have identical contents (W200)"
        in res.message_strings
    )
    assert (
        "foo.py:7: two AST branches have identical contents (W200)"
        in res.message_strings
    )
