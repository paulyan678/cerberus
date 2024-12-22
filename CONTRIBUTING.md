# Contributing to Cerberus

Thank you for improving Cerberus. Contributions should preserve reproducibility,
privacy, and the distinction between synthetic demonstrations and measured
research results.

## Development setup

Cerberus supports Python 3.10 and newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the local quality gates before submitting a change:

```bash
python scripts/demo.py
python -m pytest
python -m ruff check .
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

## Change guidelines

1. Open a focused branch and keep unrelated refactors separate.
2. Add or update tests for behavior changes, including malformed inputs and
   failure paths where relevant.
3. Update the README, CLI reference, and data contracts when an interface
   changes.
4. Use clear commit messages that explain the observable change.
5. In the pull request, describe the motivation, verification commands, API or
   schema changes, and remaining limitations.

Core logic belongs in `cerberus/`. Keep `scripts/` as thin compatibility
wrappers. CLI data belongs on standard input/output; diagnostics and progress
belong on standard error.

## Data and research claims

Do not commit `.env`, credentials, personal CCTV footage, generated private
descriptions, or other sensitive data. Add only fictional or appropriately
licensed test fixtures.

Synthetic smoke-test metrics must be labelled as synthetic. Any real research
result must include dataset provenance, consent or licensing basis, annotation
protocol, split, query set, model identifier and date, dependency versions,
metric parameters, and enough commands to reproduce the result.

## Dependency and security changes

Keep runtime dependencies minimal and bounded. Explain why a new dependency is
needed. Do not weaken finite retries, input validation, secret handling, or
remote-file cleanup. Report suspected vulnerabilities according to
[SECURITY.md](SECURITY.md), not in a public issue.

No license has been selected for the repository. A contribution does not change
that status unless the project owners explicitly adopt a license.
