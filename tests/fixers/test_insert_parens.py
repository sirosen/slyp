import textwrap

import pytest


def test_fixer_inserts_missing_parens_call_arg(fix_text):
    # awkward looking but simple case for paren insertion fixer
    # (black will fix this)
    new_text, _ = fix_text(
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


def test_fixer_inserts_missing_parens_call_arg_in_list(fix_text):
    # normal case for paren insertion fixer, in an arg list
    # black fixing will be a no-op because we already handle indents nicely for this
    new_text, _ = fix_text(
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


@pytest.mark.parametrize("trailer", ("", ",", ",  # comment"))
def test_fixer_inserts_missing_parens_around_dict_element(fix_text, trailer):
    # normal case for paren insertion fixer, in a dict element
    # black fixing will be a no-op because we already handle indents nicely for this
    new_text, _ = fix_text(
        textwrap.dedent(
            f"""\
            {{
                "foo": "bar "
                "baz"{trailer}
            }}
            """
        ),
        filename="snork.py",
    )
    assert new_text == textwrap.dedent(
        f"""\
        {{
            "foo": (
                "bar "
                "baz"
            ){trailer}
        }}
        """
    )
