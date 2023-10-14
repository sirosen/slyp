# SLYP

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
```

## Implemented Rules

E100: unnecessary string concat

    x = "foo " "bar"

E101: unparenthesized multiline string concat in keyword arg

    foo(
        bar="alpha "
        "beta"
    )

E102: unparenthesized multiline string concat in dict value

    {
        "foo": "alpha "
        "beta"
    }

E103: unparenthesized multiline string concat in collection type

    x = (  # a tuple, set or list
        "alpha "
        "beta",
        "gamma"
    )
    x = {  # e.g. a set
        "alpha "
        "beta",
    }

## License

`slyp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
