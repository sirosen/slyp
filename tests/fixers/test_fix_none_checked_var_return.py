import textwrap

import pytest


def test_none_checked_var_return_transform(fix_text):
    new_text, _ = fix_text(
        """\
        if foo is None:
            return foo
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if foo is None:
            return None
        """
    )


@pytest.mark.parametrize(
    "disable_comment",
    ("# fmt: off", "#fmt:off ", "#slyp: disable", "# slyp: disable=format "),
)
def test_none_checked_var_return_transform_disabled_with_fmt_off(
    fix_text, disable_comment
):
    fix_text(
        f"""\
        if foo is None:
            return foo{disable_comment}
        """,
        expect_changes=False,
    )


def test_none_checked_var_return_transform_preserves_leading_comment(fix_text):
    new_text, _ = fix_text(
        """\
        if foo is None:
            # explanation!
            return foo
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if foo is None:
            # explanation!
            return None
        """
    )


def test_none_checked_var_return_transform_preserves_trailing_comment(fix_text):
    new_text, _ = fix_text(
        """\
        if foo is None:
            return foo
            # explanation!
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if foo is None:
            return None
            # explanation!
        """
    )


def test_none_checked_var_return_handles_non_indented_block_case(fix_text):
    new_text, _ = fix_text(
        """\
        if foo is None: return foo
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if foo is None:
            return None
        """
    )


@pytest.mark.parametrize("infix_whitespace", ["", " ", "  ", "   "])
def test_none_checked_var_return_preserves_trailing_comment_on_non_indented_block_case(
    fix_text, infix_whitespace
):
    new_text, _ = fix_text(
        f"""\
        if foo is None: return foo{infix_whitespace}# explainer!
        """
    )
    assert new_text == textwrap.dedent(
        """\
        if foo is None:  # explainer!
            return None
        """
    )
