Development
===========

Set up an editable environment
------------------------------

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e '.[dev]'

Quality gates
-------------

Run all four commands from the repository root:

.. code-block:: bash

   python scripts/demo.py
   python -m pytest
   python -m ruff check .
   python -m sphinx -W --keep-going -b html docs docs/_build/html

The strict Sphinx invocation treats documentation warnings as failures. Open
``docs/_build/html/index.html`` after a successful build to inspect the rendered
site.

Repository structure
--------------------

``cerberus/``
   Application modules. Business logic, validation, retrieval, and evaluation
   belong here.

``scripts/``
   Thin adapters for the historical command names. Keep behavior in the package
   so it is testable without a subprocess.

``examples/``
   Fictional fixtures for the offline demonstration. Never add private footage,
   personal information, secrets, or unlicensed data.

``tests/``
   Unit and integration tests. Cover normal behavior, validation, and failures.

``docs/``
   Sphinx source. Keep the README quick and move detailed contracts here.

``data/``
   Ignored local workspace for inputs and generated outputs. Ignored does not
   mean encrypted, backed up, access-controlled, or safe to share.

Coding conventions
------------------

* Target Python 3.10 or newer and keep functions small and typed where useful.
* Put external SDK interaction behind adapters; keep deterministic logic local.
* Bound retries and waits and preserve the original exception as the cause.
* Validate data at module boundaries and return actionable error messages.
* Write data to standard output and progress or diagnostics to standard error.
* Use UTF-8 JSON/JSONL contracts documented in :doc:`data_formats`.
* Update tests and documentation in the same change as an interface.

Documentation maintenance
-------------------------

The version in ``docs/conf.py`` should match the package release. Command
examples must be runnable from the repository root. Never paste real API keys,
private filenames, or measured results without complete provenance. Clearly
label all synthetic examples.

Contribution and security policy
--------------------------------

Read ``CONTRIBUTING.md`` before preparing a pull request and ``SECURITY.md``
before reporting a vulnerability. No open-source license has been selected;
contributions do not implicitly change that status.
