import textwrap

import pytest


def test_simple_string_concat_with_matching_characteristics(fix_text):
    new_text, _ = fix_text(
        """\
        a = "foo " "bar"
        b = 'foo ' 'bar'
        c = r"foo " r"bar"
        d = u"foo " u"bar"
        e = b"foo " b"bar"
        f = br"foo " br"bar"
        g = rb"foo " rb"bar"
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = "foo bar"
        b = 'foo bar'
        c = r"foo bar"
        d = u"foo bar"
        e = b"foo bar"
        f = br"foo bar"
        g = rb"foo bar"
        """
    )


def test_fmt_toggle_can_reenable_fixing(fix_text):
    new_text, _ = fix_text(
        """\
        # slyp: disable
        # fmt: on
        a = "foo " "bar"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        # slyp: disable
        # fmt: on
        a = "foo bar"
        """
    )


def test_quote_style_mismatch_suppresses_fixing(fix_text):
    fix_text(
        """\
        a = "foo " 'bar'
        """,
        expect_changes=False,
    )


@pytest.mark.parametrize(
    "prefix_a, prefix_b",
    [
        (prefix_a, prefix_b)
        for prefix_a in ("", "r", "u", "b", "br", "rb")
        for prefix_b in ("", "r", "u", "b", "br", "rb")
        # get the cases where they differ
        if prefix_a != prefix_b and
        # but not the ones where a str and bytes are concatenated
        ("b" in prefix_a) == ("b" in prefix_b)
        # and not the special case of "br" and "rb", which are really the same
        and {prefix_a, prefix_b} != {"br", "rb"}
    ],
)
def test_prefix_mismatch_suppresses_fixing(fix_text, prefix_a, prefix_b):
    fix_text(
        f"""\
        a = {prefix_a}"foo " {prefix_b}"bar"
        """,
        expect_changes=False,
    )


def test_prefix_mismatch_is_ignored_in_special_cases(fix_text):
    new_text, _ = fix_text(
        """\
        a = br"foo " rb"bar"
        b = rb"foo " br"bar"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        a = br"foo bar"
        b = rb"foo bar"
        """
    )


def test_double_concat(fix_text):
    new_text, _ = fix_text(
        """\
        x = "foo " "bar " "baz"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        x = "foo bar baz"
        """
    )


def test_concat_fstrings(fix_text):
    new_text, _ = fix_text(
        """\
        x = f"{foo}" f"{bar}"
        y = fr"{foo}" Fr"{bar}"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        x = f"{foo}{bar}"
        y = fr"{foo}{bar}"
        """
    )


def test_concat_fstring_with_simple(fix_text):
    new_text, _ = fix_text(
        """\
        x = f"{foo}" "bar"
        y = "foo" f"{bar}"
        p = fr"{foo}" r"bar"
        q = r"foo" rf"{bar}"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        x = f"{foo}bar"
        y = f"foo{bar}"
        p = fr"{foo}bar"
        q = rf"foo{bar}"
        """
    )


def test_concat_fstring_skips_mismatched_quotes(fix_text):
    fix_text(
        """\
        x = f'{foo}' "bar"
        y = 'foo' f"{bar}"
        """,
        expect_changes=False,
    )


def test_concat_fstring_skips_if_curly_braces_present(fix_text):
    fix_text(
        """\
        x = f'{foo}' "bar{}"
        x = 'foo{}' f"{bar}"
        """,
        expect_changes=False,
    )
