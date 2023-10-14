# SLYP

Stephen Lints Your Python

[![PyPI - Version](https://img.shields.io/pypi/v/click-type-test.svg)](https://pypi.org/project/click-type-test)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/click-type-test.svg)](https://pypi.org/project/click-type-test)

-----

**Table of Contents**

- [Hi](#Hi)
- [Installation](#installation)
- [Usage](#usage)
- [Implemented Rules](#implemented-rules)
- [License](#license)

## Hi

:wave:

I'm Stephen. I'm going to lint your Python code.

I wrote this linter because nothing else out there implemented these rules, and
some of them needed CST (rather than AST), so there was no plugin framework
(e.g. flake8 plugins) which I could use.
I hope it helps you catch slyp-ups.

## Installation

`slyp` is a python package and can be run as a pre-commit hook.

On supported python versions, it should be installed with

```console
pip install slyp
```

## Usage

Either use it as a CLI tool:

```console
slyp src/
```

Or as a pre-commit hook using the following `pre-commit-config.yaml`:

```yaml
- repo: https://github.com/sirosen/slyp
  rev: 0.0.2
  hooks:
    - id: slyp
```

## Implemented Rules

### E100

'unnecessary string concat'

    x = "foo " "bar"

### E101

'unparenthesized multiline string concat in keyword arg'

    foo(
        bar="alpha "
        "beta"
    )

### E102

'unparenthesized multiline string concat in dict value'

    {
        "foo": "alpha "
        "beta"
    }

### E103

'unparenthesized multiline string concat in collection type'

    x = (  # a tuple, set or list
        "alpha "
        "beta",
        "gamma"
    )
    x = {  # e.g. a set
        "alpha "
        "beta",
    }


### W200

'two AST branches have identical contents'

    if x is True:
        return y + 1
    else:
        # some comment
        return y + 1

## License

`slyp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
