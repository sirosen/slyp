from slyp.codes import generate_reference

START_SLUG = ".. generate-reference-insert-start\n"
END_SLUG = ".. generate-reference-insert-end\n"


def main() -> None:
    print("update-generated-reference:BEGIN")
    if update_linter_rules():
        print("changes made")
    else:
        print("no changes made")
    print("update-generated-reference:END")


def update_linter_rules() -> bool:
    with open("docs/linter_rules.rst", encoding="utf-8") as fp:
        content = fp.readlines()
    new_content = []

    for line in content:
        new_content.append(line)
        if line == START_SLUG:
            break
    new_content.append("\n")
    new_content.extend(generate_reference())
    found_end_line = False
    for line in content:
        if found_end_line:
            new_content.append(line)
        elif line == END_SLUG:
            found_end_line = True
            new_content.extend(("\n", line))
    if new_content == content:
        return False

    with open("docs/linter_rules.rst", "w", encoding="utf-8") as fp:
        fp.write("".join(new_content))
    return True


if __name__ == "__main__":
    main()
