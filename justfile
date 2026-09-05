set script-interpreter := ['uv', 'run', '--script']
version := `uvx mddj read version`

bump-version VERSION: && _cog-update _bump-changelog
    uvx mddj write version "{{VERSION}}"

serve-docs:
    uvx --with 'tox-uv' tox r -e docs
    python -m http.server 8000 -d .tox/docs/doc_build

check-sdist:
    uvx --from='check-sdist==1.6.0' check-sdist --inject-junk

tag-release:
    git tag -s "{{version}}" -m "v{{version}}"

clean:
    rm -rf dist build *.egg-info .tox .venv
    find . -type d -name '__pycache__' -exec rm -r {} +


[script]
_bump-changelog:
    # /// script
    # dependencies = ["mddj"]
    # ///
    import mddj.api

    DJ = mddj.api.DJ()
    version = DJ.read.version()
    print("updating changelog.rst")
    with open("changelog.rst") as fp:
        content = fp.read()

    marker = ".. changelog-unreleased-marker"

    content = content.replace(
        marker,
        f"""\
    {marker}

    {version}
    {"-" * len(version)}
    """,
    )
    with open("changelog.rst", "w") as fp:
        fp.write(content)

_cog-update:
    uvx --from='cogapp==3.6.0' \
        --with 'mddj' --with '.' \
        cog -r README.md docs/linter_rules.rst docs/usage.rst
