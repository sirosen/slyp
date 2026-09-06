def test_check_passes_on_example_file(check_text):
    res = check_text("""
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
        """)
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


def test_disable_requires_exact_format(check_text):
    res = check_text(
        """\
        def foo():
            x = "a " "b"  # slyp disable=E100
        """,
        filename="foo.py",
    )
    assert not res.success
    assert "foo.py:2: unnecessary string concat (E100)" in res.message_strings


def test_global_enable_overrides_global_disable(check_text):
    res = check_text(
        """\
        def foo():
            x = "a " "b"
        """,
        filename="foo.py",
        enabled_codes={"E100"},
        disabled_codes={"all"},
    )
    assert not res.success
    assert "foo.py:2: unnecessary string concat (E100)" in res.message_strings


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
