import textwrap

import pytest


def test_fixer_inserts_missing_parens_call_arg(fix_text):
    # awkward looking but simple case for paren insertion fixer
    # (black will fix this)
    new_text, _ = fix_text(
        """\
        foo(x="foo"
        "bar")
        """
    )
    assert new_text == textwrap.dedent(
        """\
        foo(x=(
                "foo"
                "bar"
            ))
        """
    )


@pytest.mark.parametrize(
    "disable_comment",
    ("# fmt: off", "#fmt:off ", "#slyp: disable", "# slyp: disable=format "),
)
def test_missing_paren_transform_disabled_with_fmt_off(fix_text, disable_comment):
    fix_text(
        f"""\
        #{disable_comment}
        foo(x="foo"
        "bar")
        """,
        expect_changes=False,
    )


def test_fixer_inserts_missing_parens_call_arg_in_list(fix_text):
    # normal case for paren insertion fixer, in an arg list
    # black fixing will be a no-op because we already handle indents nicely for this
    new_text, _ = fix_text(
        """\
        foo(
            x=1,
            y="foo"
            "bar",
            z=3,
        )
        """
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
        f"""\
        {{
            "foo": "bar "
            "baz"{trailer}
        }}
        """
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


@pytest.mark.parametrize(
    "open_delim, close_delim", (("(", ")"), ("[", "]"), ("{", "}"))
)
def test_paren_insertion_in_collection_literal(fix_text, open_delim, close_delim):
    # normal case for paren insertion fixer, in a tuple/list/set
    # black fixing will be a no-op because we already handle indents nicely for this
    new_text, _ = fix_text(
        f"""\
        {open_delim}
            "foo"
            "bar",
            "baz"
        {close_delim}
        """
    )
    assert new_text == textwrap.dedent(
        f"""\
        {open_delim}
            (
                "foo"
                "bar"
            ),
            "baz"
        {close_delim}
        """
    )


@pytest.mark.parametrize(
    "open_delim, close_delim", (("(", ")"), ("[", "]"), ("{", "}"))
)
@pytest.mark.parametrize(
    "outer_open_delim, outer_close_delim", (("(", ")"), ("[", "]"))
)
def test_paren_insertion_in_nested_collection_literal(
    fix_text, open_delim, close_delim, outer_open_delim, outer_close_delim
):
    new_text, _ = fix_text(
        f"""\
        {outer_open_delim}
            {open_delim}
                "foo"
                "bar",
                "baz"
            {close_delim},
            "buzz",
        {outer_close_delim}
        """
    )
    assert new_text == textwrap.dedent(
        f"""\
        {outer_open_delim}
            {open_delim}
                (
                    "foo"
                    "bar"
                ),
                "baz"
            {close_delim},
            "buzz",
        {outer_close_delim}
        """
    )


@pytest.mark.parametrize(
    "open_delim, close_delim", (("(", ")"), ("[", "]"), ("{", "}"))
)
def test_paren_insertion_in_collection_is_noop_on_solo_string(
    fix_text, open_delim, close_delim
):
    fix_text(
        f"""\
        {open_delim}
            "foo"
            "bar"
            "baz"
        {close_delim}
        """,
        expect_changes=False,
    )


@pytest.mark.parametrize(
    "open_delim, close_delim", (("(", ")"), ("[", "]"), ("{", "}"))
)
def test_paren_insertion_in_collection_preserves_and_respaces_comments(
    fix_text, open_delim, close_delim
):
    new_text, _ = fix_text(
        f"""\
        {open_delim}
            "foo"# comment1
            "bar" # comment2
            "baz"  # comment3
            "buzz"   # comment4
            "snork",
            x
        {close_delim}
        """
    )
    assert new_text == textwrap.dedent(
        f"""\
        {open_delim}
            (
                "foo"  # comment1
                "bar"  # comment2
                "baz"  # comment3
                "buzz"  # comment4
                "snork"
            ),
            x
        {close_delim}
        """
    )
