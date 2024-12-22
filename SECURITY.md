# Security policy

Cerberus is an academic prototype and is not designed to protect people,
property, accounts, or production infrastructure. There is no guaranteed
security-support or patch timeline.

## Reporting a vulnerability

Do not disclose a vulnerability, exposed API key, or private-footage location
in a public issue. Use GitHub's private **Report a vulnerability** channel for
this repository if it is available. If it is not available, contact a listed
project maintainer privately and share only the minimum information needed to
reproduce the problem.

Include:

- the affected version or commit;
- the impacted command or component;
- reproduction steps using synthetic data;
- the potential impact; and
- any known mitigation.

Do not upload third-party footage, use another person's credentials, access data
without authorization, or test against production services beyond your own
account.

## Secrets and sensitive data

- Store `GEMINI_API_KEY` in the environment or an ignored `.env` file. Never
  place a real key in documentation, fixtures, logs, screenshots, or commits.
- Treat uploaded videos, generated descriptions, classifications, and search
  queries as potentially sensitive.
- Keep real data under an access-controlled workspace; `data/` is ignored for
  convenience, not encrypted or otherwise secured.
- Review provider retention and deletion behavior. Use `cerberus-list` and
  `cerberus-delete` to inspect and remove remote files after a run.
- Rotate a key immediately if it is exposed, then remove it from history and
  invalidate cached artifacts containing it.

## Supported scope

The maintainers aim to keep the current default branch functional. Historical
commits, modified deployments, third-party models, and downstream systems are
outside the supported scope. Dependency and hosted-model security also depends
on their respective providers.
