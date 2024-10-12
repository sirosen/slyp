# SLYP

Stephen Lints Your Python

An opinionated linter and fixer.

[![PyPI - Version](https://img.shields.io/pypi/v/slyp.svg)](https://pypi.org/project/slyp)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/slyp.svg)](https://pypi.org/project/slyp)

Full documentation: https://slyp.readthedocs.io/en/latest/index.html

-----

**Table of Contents**

- [Hi](#Hi)
- [Installation](#installation)
- [Usage](#usage)
- [Implemented Rules](#implemented-rules)
- [License](#license)

## Hi

:wave:

I'm Stephen. I'm going to lint (and fix) your Python code.

I wrote this linter because nothing else out there implemented these rules, and
some of them needed CST (rather than AST), so there was no plugin framework
(e.g. flake8 plugins) which I could use.

I hope it helps you.

## Installation

`slyp` is a python package and can be run as a pre-commit hook.

On supported python versions, it should be installed with

```console
pip install slyp
```

## Usage

Either use it as a CLI tool:

```console
slyp
```

Or as a pre-commit hook using the following `pre-commit-config.yaml`:

```yaml
- repo: https://github.com/sirosen/slyp
  rev: 0.8.1
  hooks:
    - id: slyp
```

## License

`slyp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
