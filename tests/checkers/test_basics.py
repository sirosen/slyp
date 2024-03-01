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
