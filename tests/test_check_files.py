def test_check_passes_on_example_file(check_text):
    res = check_text(
        """
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
    assert res.success


def test_check_captures_e100(check_text):
    res = check_text(
        """\
        x = "foo" "bar"
        """,
        filename="foo.py",
    )
    assert not res.success
    assert "foo.py:1: unnecessary string concat (E100)" in res.message_strings


def test_check_captures_w102(check_text):
    res = check_text(
        """\
        foo = {
            "x": "foo"
        "bar"
        }
        """,
        filename="foo.py",
    )
    assert not res.success
    assert (
        "foo.py:2: unparenthesized multiline string concat in dict value (W102)"
        in res.message_strings
    )


def test_check_captures_w103(check_text):
    res = check_text(
        """\
        foo = (
            "alpha",
            "beta"
            "gamma",
        )
        """,
        filename="foo.py",
    )
    assert not res.success
    assert (
        "foo.py:3: unparenthesized multiline string concat in collection type (W103)"
        in res.message_strings
    )


def test_check_w103_ignores_solo_strings(check_text):
    res = check_text(
        """\
        foo = [
            "alpha"
            "beta"
        ]
        """
    )
    assert res.success


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


def test_can_disable_code_with_comment(check_text):
    res = check_text(
        """\
        def foo():
            x = "a " "b"  # slyp: disable=E100
        """,
        filename="foo.py",
    )
    assert res.success


def test_can_disable_code_via_category_disable(check_text):
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
        disabled_codes={"W"},
    )
    assert res.success


def test_check_captures_e110(check_text):
    res = check_text(
        """\
        if foo is None:
            return foo
        """,
        filename="foo.py",
    )

    assert not res.success
    assert (
        "foo.py:1: returning a variable checked as None, "
        "rather than returning None (E110)"
    ) in res.message_strings
