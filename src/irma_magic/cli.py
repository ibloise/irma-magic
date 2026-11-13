import argparse
import sys

from . import constants
from .bulk import IrmaBulk, IrmaExecutionError


def main():
    parser = argparse.ArgumentParser(
        prog="irmagic",
        description="Utilities for preparing and running CDC-IRMA batches.",
    )
    parser.add_argument("--irma_cmd", default="IRMA")
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

    bulk_parser.add_argument("-f", "--files", help="Archivos que se van a utilizar", nargs="+", required=True)
    bulk_parser.add_argument("-m", "--module", help="Modulo que debe usar IRMA", required=True)
    bulk_parser.add_argument("-r", "--reads", choices=[constants.SINGLE_READS, constants.PAIRED_READS], default=constants.SINGLE_READS,
                        help="Tipo de lecturas introducidas")
    bulk_parser.add_argument("--forward_pattern", help="Patrón de la lectura forward (solo para paired)",
                        default=constants.FORWARD_VALUE)
    bulk_parser.add_argument("--reverse_pattern", help="Patrón para la lectura reverse (solo en paired)",
                        default=constants.REVERSE_VALUE)
    

    args = parser.parse_args()

    if args.command == "bulker":
        try:
            return bulker_main(args)
        except ValueError as error:
            parser.error(str(error))
        except IrmaExecutionError as error:
            print(f"irmagic: error: {error}", file=sys.stderr)
            return 1
    return 0

def bulker_main(args):

    #argparser

    # Declaramos el bulker:

    if not args.files:
        raise ValueError("Es necesario pasar archivos")
    
    irma_bulker = IrmaBulk(args.module, args.files, args.reads, args.irma_cmd, args.forward_pattern, args.reverse_pattern)

    return irma_bulker.run()


if __name__ == "__main__":
    raise SystemExit(main())
