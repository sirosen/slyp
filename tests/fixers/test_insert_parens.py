import textwrap


def test_fixer_inserts_missing_parens_call_arg(capsys, fix_text):
    # awkward looking but simple case for paren insertion fixer
    # (black will fix this)
    new_text = fix_text(
        textwrap.dedent(
            """\
            foo(x="foo"
            "bar")
            """
        ),
        filename="snork.py",
    )
    assert new_text == textwrap.dedent(
        """\
        foo(x=(
                "foo"
                "bar"
            ))
        """
    )


def test_fixer_inserts_missing_parens_call_arg_in_list(capsys, fix_text):
    # normal case for paren insertion fixer, in an arg list
    # black fixing will be a no-op because we already handle indents nicely for this
    new_text = fix_text(
        textwrap.dedent(
            """\
            foo(
                x=1,
                y="foo"
                "bar",
                z=3,
            )
            """
        ),
        filename="snork.py",
    )
    assert new_text == textwrap.dedent(
        """\
        foo(
            x=1,
            y=(
                "foo"
                "bar"
            ),
            z=3,
        )
        """
    )
