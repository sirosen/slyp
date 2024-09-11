Usage
=====

Either use it as a CLI tool:

.. code-block:: bash

    slyp

Or as a pre-commit hook using the following ``pre-commit-config.yaml``:

.. code-block:: yaml

    - repo: https://github.com/sirosen/slyp
      rev: 0.7.1
      hooks:
        - id: slyp

Options and Arguments
---------------------

.. code-block::

    slyp [files...] [-v/--verbose] [--use-git-ls] [--disable CODES] [--enable CODES]

``[files...]``: If passed positional arguments, ``slyp`` will treat them as
filenames to check. Otherwise, it will search the current directory for python files.

``-v/--verbose``: Enable more verbose output

``--use-git-ls``: Find files to check by doing a ``git ls-files`` call and filtering
the results to files which appear to be python.
This is mutually exclusive with any filename arguments.

``--disable CODES``: Pass a comma-delimited list of codes to turn off.

``--enable CODES``: Pass a comma-delimited list of codes to turn on.

