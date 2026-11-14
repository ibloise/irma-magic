import argparse
import os
import sys

from . import constants
from .bulk import IrmaBulk, IrmaExecutionError
from . import flu_tools, renamer


def _execute(callback, args):
    try:
        return callback(args)
    except ValueError as error:
        print(f"irmagic: error: {error}", file=sys.stderr)
        return 2
    except (OSError, IrmaExecutionError) as error:
        print(f"irmagic: error: {error}", file=sys.stderr)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="irmagic",
        description="Utilities for preparing and running CDC-IRMA batches.",
    )
    parser.add_argument(
        "--irma-cmd",
        "--irma_cmd",
        dest="irma_cmd",
        default="IRMA",
        help="IRMA executable (default: IRMA)",
    )
    subparser = parser.add_subparsers(
        dest="command",
        required=True,
        help="available commands",
    )

    bulk_parser = subparser.add_parser(
        "bulker",
        help="run IRMA for single-end or paired FASTQ inputs",
        description="Build and run one IRMA command per sample.",
    )
    bulk_parser.add_argument(
        "--irma-cmd",
        "--irma_cmd",
        dest="irma_cmd",
        default=argparse.SUPPRESS,
        help="IRMA executable (overrides the global option)",
    )
    bulk_parser.add_argument(
        "-f", "--files", nargs="+", required=True, help="Input FASTQ files"
    )
    bulk_parser.add_argument("-m", "--module", required=True, help="IRMA module to run")
    bulk_parser.add_argument(
        "-r",
        "--reads",
        choices=[constants.SINGLE_READS, constants.PAIRED_READS],
        default=constants.SINGLE_READS,
        help="Read layout (default: single)",
    )
    bulk_parser.add_argument(
        "--forward-pattern",
        "--forward_pattern",
        dest="forward_pattern",
        default=constants.FORWARD_VALUE,
        help="Forward read marker for paired input",
    )
    bulk_parser.add_argument(
        "--reverse-pattern",
        "--reverse_pattern",
        dest="reverse_pattern",
        default=constants.REVERSE_VALUE,
        help="Reverse read marker for paired input",
    )

    renamer_parser = subparser.add_parser(
        "renamer",
        help="rename and copy CDC-IRMA output files",
        description="Copy CDC-IRMA output files to a destination directory.",
    )
    renamer.add_arguments(renamer_parser)

    flu_parser = subparser.add_parser(
        "flu",
        help="process influenza FASTA files",
        description="Group influenza FASTA records by sample or segment subtype.",
    )
    flu_tools.add_arguments(flu_parser)

    args = parser.parse_args(argv)

    if args.command == "bulker":
        return _execute(bulker_main, args)
    elif args.command == "renamer":
        return _execute(renamer.run, args)
    elif args.command == "flu":
        return _execute(flu_tools.run, args)
    return 0


def bulker_main(args):
    if not args.files:
        raise ValueError("At least one FASTQ input is required")
    irma_bulker = IrmaBulk(
        args.module,
        args.files,
        args.reads,
        args.irma_cmd,
        args.forward_pattern,
        args.reverse_pattern,
    )
    missing_inputs = [path for path in args.files if not os.path.isfile(path)]
    if missing_inputs:
        raise ValueError(
            "FASTQ input file(s) do not exist or are not regular files: "
            + ", ".join(repr(path) for path in missing_inputs)
        )
    return irma_bulker.run()


if __name__ == "__main__":
    raise SystemExit(main())
