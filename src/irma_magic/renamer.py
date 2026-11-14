import argparse
import os
import shutil
import sys

from . import constants, files
from .fasta import FastaFile, FastaRecord


def _preflight(renamers):
    destinations = [os.path.abspath(item.dest_file) for item in renamers]
    normalized = [os.path.normcase(path) for path in destinations]
    if len(set(normalized)) != len(normalized):
        raise FileExistsError("Multiple inputs map to the same output path")
    existing = [path for path in destinations if os.path.lexists(path)]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite output file(s): " + ", ".join(existing)
        )


def _run(renamers, out_dir):
    _preflight(renamers)
    os.makedirs(out_dir, exist_ok=True)
    for renamer in renamers:
        try:
            renamer.rename()
        except (OSError, ValueError) as error:
            raise type(error)(
                f"Failed to process {renamer.full_name!r} as "
                f"{renamer.dest_file!r}: {error}"
            ) from error


class IrmaRenamer(files.File):
    def __init__(self, filename, out_dir=None):
        super().__init__(filename)
        self.out_dir = os.path.abspath(os.fspath(out_dir or os.curdir))
        source_dir_name = os.path.basename(os.path.normpath(self.path))
        prefix = f"{source_dir_name}_" if source_dir_name else ""
        self.dest_file = os.path.join(self.out_dir, prefix + self.name)

    def rename(self):
        os.makedirs(self.out_dir, exist_ok=True)

        def copy_contents(destination):
            with open(self.full_name, "rb") as source:
                shutil.copyfileobj(source, destination)

        files.write_new_file(self.dest_file, copy_contents, binary=True)
        return self.dest_file


class FastaRenamer(IrmaRenamer):
    def rename(self):
        name = os.path.splitext(os.path.basename(self.dest_file))[0]
        try:
            records = FastaFile(self.full_name).read()
        except OSError as error:
            raise ValueError(
                f"Cannot read FASTA input {self.full_name!r}: {error}"
            ) from error
        if not records:
            raise ValueError(f"FASTA file {self.full_name!r} contains no records")

        renamed_records = []
        seen_ids = set()
        for record in records:
            if record.id == name or record.id.startswith(name + "_"):
                new_id = record.id
            else:
                new_id = f"{name}_{record.id}"
            if new_id in seen_ids:
                raise ValueError(
                    f"Renaming {self.full_name!r} would create duplicate FASTA ID {new_id!r}"
                )
            seen_ids.add(new_id)
            renamed_records.append(FastaRecord(new_id, record.sequence, record.description))

        os.makedirs(self.out_dir, exist_ok=True)
        FastaFile(self.dest_file).write(renamed_records)
        return self.dest_file


class IrmaDirRenamer:
    def __init__(self, dir, types, renamer_dict, out_dir=None):
        if not os.path.isdir(dir):
            raise ValueError(f"Source path is not a directory: {dir!r}")
        self.src_dir = os.path.abspath(os.fspath(dir))
        self.out_dir = os.path.abspath(os.fspath(out_dir or os.curdir))
        self.renamer_dict = renamer_dict
        self.types = types
        self._validate_dict()

    def _validate_dict(self):
        for file_type in self.types:
            if file_type not in self.renamer_dict:
                raise ValueError(f"Type {file_type} not present in renamer dict")

    def _planned_renamers(self):
        renamers = []
        names = sorted(os.listdir(self.src_dir))
        for file_type in self.types:
            suffix = f".{file_type.lstrip('.')}"
            for name in names:
                source = os.path.join(self.src_dir, name)
                if os.path.isfile(source) and name.endswith(suffix):
                    renamers.append(self.renamer_dict[file_type](source, self.out_dir))
        return renamers

    def rename_files(self):
        renamers = self._planned_renamers()
        _run(renamers, self.out_dir)
        return [item.dest_file for item in renamers]


def add_arguments(parser):
    parser.add_argument("-d", "--dirs", nargs="+", required=True)
    parser.add_argument(
        "-t", "--types", nargs="+",
        choices=[constants.FASTA_FILE, constants.VCF_FILE, constants.BAM_FILE],
        required=True,
    )
    parser.add_argument(
        "--out-dir", "--out_dir", dest="out_dir", help="Output directory"
    )
    return parser


def run(args):
    renamer_dict = {
        constants.FASTA_FILE: FastaRenamer,
        constants.BAM_FILE: IrmaRenamer,
        constants.VCF_FILE: IrmaRenamer,
    }
    invalid_dirs = [directory for directory in args.dirs if not os.path.isdir(directory)]
    if invalid_dirs:
        raise ValueError("Source path(s) are not directories: " + ", ".join(invalid_dirs))

    planned = []
    for directory in args.dirs:
        planned.extend(
            IrmaDirRenamer(directory, args.types, renamer_dict, args.out_dir)
            ._planned_renamers()
        )
    out_dir = os.path.abspath(os.fspath(args.out_dir or os.curdir))
    _run(planned, out_dir)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rename CDC-IRMA output files")
    add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except ValueError as error:
        print(f"irmagic: error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"irmagic: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
