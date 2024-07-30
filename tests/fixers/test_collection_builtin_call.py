import textwrap


def test_dict_call_fixer_converts_empty_call_to_empty_literal(fix_text):
    new_text, _ = fix_text(
        """\
        x = dict()
        """
    )
    assert new_text == textwrap.dedent(
        """\
        x = {}
        """
    )


def test_dict_call_fixer_converts_kwargs_to_quoted_keys(fix_text):
    new_text, _ = fix_text(
        """\
        a = dict(x=1, y="foo", z_arg={})
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {"x": 1, "y": "foo", "z_arg": {}}
        """
    )


def test_dict_call_fixer_preserves_double_star_expansion(fix_text):
    new_text, _ = fix_text(
        """\
        a = dict(x=1, **kwargs)
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {"x": 1, **kwargs}
        """
    )


def test_dict_call_fixer_handles_multi_doublestar(fix_text):
    new_text, _ = fix_text(
        """\
        a = dict(x=1, **kwargs, **kwargs2)
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {"x": 1, **kwargs, **kwargs2}
        """
    )


def test_dict_call_fixer_does_not_munge_positional_arg(fix_text):
    fix_text(
        """\
        a = dict([("x", 1)])
        b = dict([("x", 1)], y=2)
        c = dict(some_func(), y=2)
        d = dict(some_func(), **other)
        e = dict(some_name, **other)
        f = dict(some_name)
        """,
        expect_changes=False,
    )


def test_dict_call_fixer_handles_nested_calls(fix_text):
    new_text, _ = fix_text(
        """\
        a = dict(x=dict(y=2))
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {"x": {"y": 2}}
        """
    )


def test_dict_call_fixer_preserves_the_simplest_whitespace(fix_text):
    new_text, _ = fix_text(
        """\
        a = dict(
            x=dict(
                y=2,
            ),
        )
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {
            "x": {
                "y": 2,
            },
        }
        """
    )


def test_set_fixer_converts_call_of_generator(fix_text):
    new_text, _ = fix_text(
        """\
        a = set(x for x in y())
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {x for x in y()}
        """
    )


def test_list_fixer_converts_call_of_generator(fix_text):
    new_text, _ = fix_text(
        """\
        a = list(x for x in y())
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = [x for x in y()]
        """
    )


def test_generator_comp_fixer_requires_exactly_one_arg(fix_text):
    # these usages are syntactically valid but semantically incorrect
    # however, the fixer should ignore them as "not my problem"
    fix_text(
        """\
        a = set((x for x in y()), True)
        b = list((x for x in y()), True)
        """,
        expect_changes=False,
    )
