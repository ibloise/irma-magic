# IRMagic

IRMagic provides Python utilities for preparing FASTQ batches for CDC-IRMA and
processing influenza FASTA results. It packages the `irma_magic` module and
the `irmagic` command with `bulker`, `renamer`, and `flu` operations. CDC-IRMA
itself is an external program and must be installed and available separately;
IRMagic does not install or bundle it.

## Install

From a checkout:

```sh
python -m pip install .
irmagic --help
```

Python 3.12 or newer is required.
IRMagic has no Python runtime dependencies. Building/installing it uses the
`setuptools>=61` backend declared in `pyproject.toml`.

## Run an IRMA batch

Pass one or more single-end FASTQ files to `bulker`. Supported suffixes are
`.fastq`, `.fq`, `.fastq.gz`, and `.fq.gz`:

```sh
irmagic --irma_cmd IRMA bulker --files reads/sample-a.fastq reads/sample-b.fq \
  --module MODULE
```

For paired reads, filenames must contain exactly one read marker each, and
each sample must have one forward and one reverse file. By default the markers
are `_R1` and `_R2`; they can be changed with `--forward_pattern` and
`--reverse_pattern`:

```sh
irmagic --irma_cmd IRMA bulker --files reads/sample-a_R1.fastq.gz reads/sample-a_R2.fastq.gz \
  --module MODULE --reads paired
```

Paths are passed as individual process arguments, including paths with spaces.
The sample ID is the filename stem with the read marker removed for paired
inputs. It becomes the IRMA output name. Duplicate output names, incomplete
pairs, unsupported file names, and IRMA execution failures are reported
explicitly. Invalid CLI arguments exit with status 2; IRMA execution errors
exit with status 1. IRMA's own output and result format are controlled by the
external IRMA installation and selected module.

## Process influenza FASTA results

`flu` accepts FASTA record IDs in the form
`<sample>_<A|B>_<segment>[_<Hn|Nn>]`. Sample IDs may contain underscores but
not whitespace. Segments are `PB2`, `PB1`, `PA`, `NP`, `HA`, `NA`, `MP`, and
`NS`; subtype suffixes are accepted on influenza A HA (`Hn`) and NA (`Nn`).
The parser preserves sequence text and does not validate nucleotide alphabets.

Export records grouped by sample:

```sh
irmagic flu --files results.fasta --mode samples --out_dir exported
```

Export records grouped by segment and complete subtype:

```sh
irmagic flu --files results.fasta --mode segments --out_dir exported
```

The `samples` mode writes one non-empty FASTA per valid sample. The `segments`
mode writes names such as `HA_H3N2.fasta`, `NA_H3N2.fasta`, and
`MP_H3N2.fasta`. A sample without a complete A subtype is reported and omitted
from subtype groups; other samples continue. A partial batch exits with status
1. Invalid input or output collisions also fail explicitly. CSV summary helpers
in `irma_magic.flu_tools.FluGenomeSummarizer` write standard CSV to an open text
handle using the standard library. Add `--summary` to `irmagic flu` to create
`summary.csv` in the output directory; existing summaries are not overwritten.

The `renamer` command copies selected IRMA output files without modifying their
sources and refuses to overwrite existing or colliding output paths:

```sh
irmagic renamer --dirs irma-run --types fasta vcf --out_dir renamed
```

## Limits

Unit and integration tests use synthetic files and simulated IRMA subprocesses;
the suite does not require a CDC-IRMA installation. No real IRMA execution,
clinical validation, or biological validation is claimed. See
[`docs/development/H4-report.md`](docs/development/H4-report.md) for current
verification evidence and known limitations.

## Development

See [`docs/development/README.md`](docs/development/README.md) for the
development milestones and [`AGENTS.md`](AGENTS.md) for repository conventions.
The project is distributed under the MIT License; see [LICENSE](LICENSE).
