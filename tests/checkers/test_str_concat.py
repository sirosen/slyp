def test_check_captures_e100(check_text):
    res = check_text(
        """\
        x = "foo" "bar"
        """,
        filename="foo.py",
    )
    assert not res.success
    assert "foo.py:1: unnecessary string concat (E100)" in res.message_strings


def test_check_captures_e101(check_text):
    res = check_text(
        """\
        x = "foo" + "bar"
        """,
        filename="foo.py",
    )
    assert not res.success
    assert "foo.py:1: unnecessary string concat with plus (E101)" in res.message_strings


def test_check_captures_e101_multiline(check_text):
    res = check_text(
        """\
        x = '''foo
        ''' + "bar"
        """,
        filename="foo.py",
    )
    assert not res.success
    assert "foo.py:2: unnecessary string concat with plus (E101)" in res.message_strings
