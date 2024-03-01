def test_check_captures_w200(check_text):
    res = check_text(
        """\
        def foo():
            if bar():
                return baz(quux("snork"))
            else:
                return baz(quux("snork"))
        """,
        filename="foo.py",
    )

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
