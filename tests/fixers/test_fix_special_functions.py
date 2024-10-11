import textwrap


def test_unannotated_init_gets_return_none_added(fix_text):
    new_text, _ = fix_text(
        """\
        class A:
            def __init__(self): ...
        """
    )
    assert new_text == textwrap.dedent(
        """\
        class A:
            def __init__(self) -> None: ...
        """
    )


def test_annotated_init_sees_no_change(fix_text):
    fix_text(
        """\
        class A:
            def __init__(self) -> None: ...
        """,
        expect_changes=False,
    )


def test_badly_annotated_init_sees_no_change(fix_text):
    # this annotation is fundamentally *wrong*, but it should be ignored by the fixer
    fix_text(
        """\
        class A:
            def __init__(self) -> A: ...
        """,
        expect_changes=False,
    )


def test_mixed_arg_annotations_dont_change_init_type(fix_text):
    new_text, _ = fix_text(
        """\
        class A:
            def __init__(self, x: int, y): ...
        """
    )
    assert new_text == textwrap.dedent(
        """\
        class A:
            def __init__(self, x: int, y) -> None: ...
        """
    )
