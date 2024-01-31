#!/usr/bin/env python
import re
import sys


def get_old_version():
    with open("pyproject.toml") as fp:
        content = fp.read()
    match = re.search(r'^version = "(\d+\.\d+\.\d+)"$', content, flags=re.MULTILINE)
    if not match:
        raise ValueError("did not find old version in pyproject.toml")
    return match.group(1)


def replace_version(filename, prefix, old_version, new_version):
    print(f"updating {filename}")
    with open(filename) as fp:
        content = fp.read()
    old_str = prefix + old_version
    new_str = prefix + new_version
    content = content.replace(old_str, new_str)
    with open(filename, "w") as fp:
        fp.write(content)


def update_changelog(new_version):
    print("updating CHANGELOG.md")
    with open("CHANGELOG.md") as fp:
        content = fp.read()

    marker = "<!-- changelog-unreleased-marker -->"

    content = content.replace(
        marker,
        f"""{marker}

# {new_version}""",
    )
    with open("CHANGELOG.md", "w") as fp:
        fp.write(content)


def parse_version(s):
    vals = s.split(".")
    if len(vals) != 3:
        raise ValueError(f"invalid version string: {s}")
    return tuple(int(x) for x in vals)


def comparse_versions(old_version, new_version):
    if parse_version(new_version) <= parse_version(old_version):
        raise ValueError("new version must be greater than old version")


def main():
    if len(sys.argv) != 2:
        sys.exit(2)

    new_version = sys.argv[1]
    old_version = get_old_version()
    print(f"old = {old_version}, new = {new_version}")
    comparse_versions(old_version, new_version)

    replace_version("pyproject.toml", 'version = "', old_version, new_version)
    replace_version("README.md", "rev: ", old_version, new_version)
    update_changelog(new_version)


if __name__ == "__main__":
    main()
