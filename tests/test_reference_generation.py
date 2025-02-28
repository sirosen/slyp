from slyp.codes import ALL_CODES, generate_reference


def test_generated_reference_shows_and_hides_codes_by_hidden():
    doc = "".join(generate_reference())
    for code_def in ALL_CODES:
        if code_def.hidden:
            assert code_def.code not in doc
        else:
            assert code_def.code in doc
