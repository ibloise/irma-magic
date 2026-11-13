# IRMagic

IRMagic provides Python utilities for preparing CDC-IRMA batches and processing
their FASTA results. The `irma-magic` distribution installs the `irma_magic`
Python package and the `irmagic` command.

Install from a local checkout with:

```sh
python -m pip install .
irmagic --help
```

CDC-IRMA is an external program. Installing IRMagic does not install CDC-IRMA;
commands that execute IRMA require a separate, working IRMA installation.

The `flu_tools` module uses only the Python standard library for FASTA and CSV
processing. Summary CSV methods accept an open text handle and write a header
followed by one or more rows.
