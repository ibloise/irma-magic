# Development

## Setup and checks

Use Python 3.8 or newer. The test suite uses only the standard library and
synthetic input files; CDC-IRMA is not needed to run it.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```

The CI workflow runs the unit/integration suite on the Python versions listed
in `pyproject.toml`. Tests that exercise IRMA execution replace the subprocess
backend with a deterministic mock; they do not call the real IRMA program.

## Contribution workflow

- Start focused development from `develop` in a `codex/<short-feature-name>`
  branch.
- Follow the repository `AGENTS.md`; use conventional commit messages.
- Keep fixtures synthetic and small. Add tests for behavior changes and report
  commands and outcomes accurately.
- Open a pull request targeting `develop` for review. Do not merge, tag, or
  publish without explicit maintainer approval.

No lint or type-check tool is configured. Do not add one without agreement.
