import textwrap


def test_none_checked_var_ifexp_transform(fix_text):
    new_text, _ = fix_text("""\
        x = var if var is None else f(var)
        """)
    assert new_text == textwrap.dedent("""\
        x = None if var is None else f(var)
        """)


def test_none_checked_var_negated_ifexp_transform(fix_text):
    new_text, _ = fix_text("""\
        x = f(var) if var is not None else var
        """)
    assert new_text == textwrap.dedent("""\
        x = f(var) if var is not None else None
        """)
