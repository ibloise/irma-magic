# Code cleanup report

## Confirmed findings

- `FastaFile.write()` opened the destination with mode `w`, so it could truncate
  an existing file. A serialization failure could also leave a partial FASTA.
- FASTA, CSV summary, and copied-file writes had separate overwrite and cleanup
  behavior. The existence checks before opening were vulnerable to races.
- The main CLI routed execution and I/O errors through `argparse.parser.error()`,
  presenting them as syntax errors with exit status 2.
- `return_genomes()` and `return_genomes_with_errors()` repeated sample grouping.
  Paired FASTQ marker parsing was repeated between pairing and `FastqSet` setup.
- The legacy `setup.py` is already absent from `develop`; `pyproject.toml` is the
  only package configuration and contains no runtime dependency list.

## Changes made

- Added a small standard-library `write_new_file()` helper. It writes to an
  exclusive temporary file in the destination directory, then publishes by
  creating a hard link. An existing destination is never replaced, and a failed
  write does not publish partial contents. FASTA, CSV summaries, and renamer
  copies use this path.
- Split influenza export into group validation, destination planning, and file
  writing. A mid-batch failure keeps completed outputs and cleans the staging
  file for the failed output. No rollback is attempted.
- Shared genome grouping while preserving strict and per-sample-error policies.
  Paired FASTQ sample names are passed from pairing into `FastqSet` to avoid
  parsing the same marker twice.
- Standardized CLI help and visible messages in English. Hyphenated options are
  primary; underscore forms remain aliases. Invalid arguments/inputs return 2;
  processing failures and partial batches return 1; successful runs return 0.
  Operational errors no longer use argparse syntax formatting.
- Added CLI input-file checks for `bulker`, contextual FASTA/renamer errors, and
  regression coverage for partial writes, batch failures, output collisions,
  exit codes, and both option spellings.
- Removed the undocumented `FileWriterInterface` stub; `FastaFileWriter` and the
  writer injection point remain. The stub had no behavior or distinct contract.
- Updated the README with the output-retention policy and added a CI job to build
  wheel and sdist, install each in a fresh virtual environment, and run the
  installed `irmagic` command.

## Batch policy

- Completed IRMagic-created files are retained after a later file fails. The
  current failed output is never published; pre-existing destinations remain
  unchanged. The command stops and returns 1.
- A sample rejected during influenza grouping is reported, other valid samples
  continue, and the command returns 1 for the partial result.
- `bulker` stops at the first IRMA failure and keeps outputs from earlier
  samples. IRMagic does not remove files from the failing external IRMA process,
  since it does not control that process's output layout.

## Validation

- `PYTHONPATH=src python -m unittest discover -s tests -v`: **85 tests passed**
  on Python 3.13.5.
- `python -m compileall -q src tests` and `git diff --check`: passed.
- Built wheel and sdist locally. Installed the wheel with `--no-deps` in a fresh
  Python 3.13 virtual environment, then verified package import and help for
  `irmagic` and all three subcommands from outside the checkout.
- Wheel and sdist metadata identify distribution `irma-magic`, package
  `irma_magic`, version `0.1.0a1`, MIT, Python `>=3.10`, and no `Requires-Dist`.
- GitHub Actions run [#6](https://github.com/ibloise/irma-magic/actions/runs/43592652275)
  passed: unit tests on Python 3.10–3.14 and wheel/sdist build plus clean install
  and CLI checks on Python 3.10. Only Python 3.13.5 is installed locally.

## Risks and pending decisions

- Atomic publication uses a same-directory hard link. If the destination
  filesystem does not support hard links, the write fails without publishing an
  output; this behavior has not been checked on non-local filesystems.
- A failing external IRMA run can leave its own partial output. Cleanup is
  intentionally not attempted without a verified output contract.
- `renamer` still returns success when a valid source directory contains no
  files matching the selected types. Whether this should become a warning or an
  invalid-input error is ambiguous, so existing behavior was retained.
- The `project.license` table still triggers a setuptools deprecation warning
  with newer setuptools. Changing the syntax may affect the declared
  `setuptools>=61` compatibility range and remains a separate packaging choice.
- `FileWriterInterface` was directly importable from `flu_tools`, although it
  was undocumented and not exported from the package. Its removal is the only
  direct import compatibility change in this cleanup.
- No CDC-IRMA installation or biological/clinical validation was used.
