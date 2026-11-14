"""Small FASTA reader and writer for the formats used by IRMagic."""

from dataclasses import dataclass
from typing import Iterable, List, TextIO

from .files import write_new_file


@dataclass
class FastaRecord:
    """One FASTA record, with the identifier and remaining header text split."""

    id: str
    sequence: str
    description: str = ""

    def __post_init__(self):
        self.id = self.id.strip()
        self.description = self.description.strip()
        if not self.id:
            raise ValueError("FASTA record identifier cannot be empty")
        if not self.sequence:
            raise ValueError(f"FASTA record {self.id!r} has an empty sequence")


class FastaParser:
    """Parse FASTA records from a text stream without validating alphabets."""

    @staticmethod
    def parse(handle: TextIO) -> Iterable[FastaRecord]:
        record_id = None
        description = ""
        sequence_parts = []

        for line_number, line in enumerate(handle, start=1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue

            if line.startswith(">"):
                if record_id is not None:
                    yield FastaRecord(record_id, "".join(sequence_parts), description)
                elif sequence_parts:
                    raise ValueError(
                        f"FASTA sequence found before the first header at line {line_number}"
                    )

                header = line[1:].strip()
                if not header:
                    raise ValueError(f"Empty FASTA header at line {line_number}")
                header_parts = header.split(None, 1)
                record_id = header_parts[0]
                description = header_parts[1] if len(header_parts) == 2 else ""
                sequence_parts = []
            else:
                if record_id is None:
                    raise ValueError(
                        f"FASTA sequence found before the first header at line {line_number}"
                    )
                sequence_parts.append("".join(line.split()))

        if record_id is not None:
            yield FastaRecord(record_id, "".join(sequence_parts), description)


class FastaWriter:
    """Write FASTA records with a stable, configurable sequence line width."""

    def __init__(self, line_width: int = 60):
        if line_width < 1:
            raise ValueError("FASTA line width must be a positive integer")
        self.line_width = line_width

    def write(self, records: Iterable[FastaRecord], handle: TextIO) -> None:
        for record in records:
            header = record.id
            if record.description:
                header = f"{header} {record.description}"
            handle.write(f">{header}\n")
            for offset in range(0, len(record.sequence), self.line_width):
                handle.write(record.sequence[offset:offset + self.line_width] + "\n")


class FastaFile:
    """Read and write FASTA records at a filesystem path."""

    def __init__(self, path: str, line_width: int = 60):
        self.path = path
        self.writer = FastaWriter(line_width=line_width)

    def read(self) -> List[FastaRecord]:
        with open(self.path, "r", encoding="utf-8") as handle:
            try:
                return list(FastaParser.parse(handle))
            except ValueError as error:
                raise ValueError(
                    f"Invalid FASTA file {self.path!r}: {error}"
                ) from error

    def write(self, records: Iterable[FastaRecord]) -> None:
        write_new_file(
            self.path,
            lambda handle: self.writer.write(records, handle),
            newline="\n",
        )
