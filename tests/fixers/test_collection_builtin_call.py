import textwrap

import pytest


@pytest.mark.parametrize(
    "original_text, fixed_text",
    [
        ("dict()", "{}"),
        ("list()", "[]"),
        ("tuple()", "()"),
    ],
)
def test_builtin_call_fixer_converts_empty_call_to_empty_literal(
    fix_text, original_text, fixed_text
):
    new_text, _ = fix_text(f"x = {original_text}")
    assert new_text == f"x = {fixed_text}"


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
    # trailing comma whitespace + leading whitespace is the simple case
    # because the trailing comma carries the whitespace info, it's easy to
    # preserve by just keeping the comma intact
    new_text, _ = fix_text(
        """\
        a = dict(
            x=dict(
                y=2,
            ),
            z=dict(
                **p,
            )
        )
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {
            "x": {
                "y": 2,
            },
            "z": {
                **p,
            }
        }
        """
    )


def test_dict_call_fixer_preserves_intricate_whitespace(fix_text):
    # no trailing comma, or empty block are more intricate cases
    # we need to find the whitespace which is attached to the last arg
    # and reattach it to the rbrace
    new_text, _ = fix_text(
        """\
        a = dict(
            x=dict(
                    y="hi"
            ),
            z=dict(

            ),
            p=dict(

                **q
        )
        )
        """
    )
    assert new_text == textwrap.dedent(
        """\
        a = {
            "x": {
                    "y": "hi"
            },
            "z": {

            },
            "p": {

                **q
        }
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


@pytest.mark.parametrize("set_variant", ("set", "frozenset"))
@pytest.mark.parametrize(
    "expression, unwrapped",
    (
        ("set(foo)", "foo"),
        ("list(foo)", "foo"),
        ("sorted(foo)", "foo"),
        ("sorted(foo, reversed=True)", "foo"),
        ("reversed(foo)", "foo"),
        ("tuple(foo)", "foo"),
        ("set(tuple(foo))", "foo"),
        ("set()", ""),
        ("frozenset()", ""),
    ),
)
def test_iterable_call_under_set_call_is_unwrapped(
    fix_text, set_variant, expression, unwrapped
):
    new_text, _ = fix_text(f"{set_variant}({expression})")
    assert new_text == f"{set_variant}({unwrapped})"


def test_nested_iterable_calls_under_set_work(fix_text):
    # this is a regression test for a bug in which testing on the `original_node` led
    # to an incorrect conclusion being drawn about the `updated_node`
    new_text, _ = fix_text(
        """\
        set(tuple())
        set(list())
        """
    )
    assert new_text == textwrap.dedent(
        """\
        set(())
        set([])
        """
    )
