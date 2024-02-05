import textwrap

import pytest


def test_simple_string_concat_with_matching_characteristics(fix_text):
    new_text = fix_text(
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
    ],
)
def test_prefix_mismatch_suppresses_fixing(fix_text, prefix_a, prefix_b):
    fix_text(
        f"""\
        a = {prefix_a}"foo " {prefix_b}"bar"
        """,
        expect_changes=False,
    )


def test_double_concat(fix_text):
    new_text = fix_text(
        """\
        x = "foo " "bar " "baz"
        """,
    )
    assert new_text == textwrap.dedent(
        """\
        x = "foo bar baz"
        """
    )
