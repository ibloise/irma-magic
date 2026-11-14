import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from typing import Optional

from . import constants
from .fasta import FastaFile, FastaRecord
from .files import write_new_file


SEGMENTS = [
    constants.PB2,
    constants.PB1,
    constants.PA,
    constants.NP,
    constants.HA,
    constants.NA,
    constants.M,
    constants.NS
]

class FluSegment:

    A_TYPE = constants.A_TYPE
    B_TYPE = constants.B_TYPE

    SEGMENTS_METADATA = {
        constants.PB2: {
            "name":  "PB2"
        },
        constants.PB1: {
            "name": "PB1"
        },
        constants.PA: {
            "name": "PA"
        },
        constants.NP: {
            "name": "Nucleoprotein"
        },
        constants.HA: {
            "name": "Hemagglutinin"
        },
        constants.NA: {
            "name": "Neuraminidase"
        },
        constants.M: {
            "name": "Matrix"
        },
        constants.NS: {
            "name": "NS"
        }
    }

    def __init__(
        self,
        id: str,
        segment: str,
        sequence: str,
        flu_type: str,
        segment_type: Optional[str],
    ) -> None:
        if not isinstance(id, str) or not id.strip():
            raise ValueError("Flu segment sample ID cannot be empty")
        if any(character.isspace() for character in id):
            raise ValueError("Flu segment sample ID cannot contain whitespace")
        if flu_type not in (self.A_TYPE, self.B_TYPE):
            raise ValueError(f"Unsupported influenza type: {flu_type!r}")
        if segment not in SEGMENTS:
            raise ValueError(f"Unsupported influenza segment: {segment!r}")
        if sequence is None or len(sequence) == 0:
            raise ValueError("Flu segment sequence cannot be empty")
        if segment_type is not None:
            expected_prefix = {constants.HA: "H", constants.NA: "N"}.get(segment)
            if flu_type != self.A_TYPE or expected_prefix is None:
                raise ValueError(
                    f"Subtype is not valid for influenza {flu_type} segment {segment}"
                )
            if not isinstance(segment_type, str) or not re.fullmatch(
                rf"{expected_prefix}\d+", segment_type
            ):
                raise ValueError(
                    f"Invalid subtype {segment_type!r} for segment {segment}"
                )

        self.id = id
        self.segment = segment
        self.type = flu_type

        if segment in [constants.NA, constants.HA] and flu_type == self.A_TYPE:
            self.segment_type = segment_type
        else:
            self.segment_type = None

        self.sequence = sequence # Property...
        self.length = len(self.sequence)

    def __repr__(self) -> str:
        return f"Flu Segment: {self.segment}-{self.SEGMENTS_METADATA[self.segment]['name']} - Length: {self.length}"

    @staticmethod
    def parse_id(record_id):
        """Parse `<sample>_<A|B>_<segment>[_Hn|Nn]` FASTA identifiers.

        Sample IDs may contain underscores but not whitespace. Segment suffixes
        are accepted only for type A HA (`Hn`) and NA (`Nn`) records.
        """
        if not isinstance(record_id, str):
            raise ValueError("FASTA record ID must be text")
        segment_pattern = "|".join(re.escape(segment) for segment in SEGMENTS)
        segment_names = "|".join(SEGMENTS)
        pattern = rf"(.+)_([AB])_({segment_pattern})(?:_([HN]\d+))?"
        match = re.fullmatch(pattern, record_id)
        if match is None:
            raise ValueError(
                f"Invalid influenza FASTA ID {record_id!r}; expected "
                f"<sample>_<A|B>_<{segment_names}>[_<Hn|Nn>]"
            )

        sample_id, flu_type, segment, segment_type = match.groups()
        if any(character.isspace() for character in sample_id):
            raise ValueError(
                f"Sample ID in FASTA record {record_id!r} cannot contain whitespace"
            )
        if segment_type is not None:
            expected_prefix = {constants.HA: "H", constants.NA: "N"}.get(segment)
            if flu_type != constants.A_TYPE or expected_prefix is None:
                raise ValueError(
                    f"Subtype suffix is not valid for influenza {flu_type} "
                    f"segment {segment} in ID {record_id!r}"
                )
            if not segment_type.startswith(expected_prefix):
                raise ValueError(
                    f"Subtype {segment_type!r} does not match segment "
                    f"{segment} in ID {record_id!r}"
                )
        return sample_id, flu_type, segment, segment_type

    @classmethod
    def from_record(cls, record):
        sample_id, flu_type, segment, segment_type = cls.parse_id(record.id)
        return cls(
            sample_id,
            segment,
            sequence=record.sequence,
            flu_type=flu_type,
            segment_type=segment_type,
        )

    @classmethod
    def read_file(cls, file):
        records = FastaFile(file).read()
        if not records:
            raise ValueError(f"FASTA file {file!r} contains no records")
        if len(records) > 1:
            raise ValueError("Only single-fasta segment are admitted")
        return cls.from_record(records[0])


class Collection: # Meter como abstract class
    CLASS_TYPE = None

    def __init__(self, *elements) -> None:
        self._collection = []
        self.extend(*elements)

    def append(self, element):
        if not isinstance(element, self.CLASS_TYPE):
            raise TypeError(
                f"{self.__class__.__name__} only accepts "
                f"{self.CLASS_TYPE.__name__} objects, got {type(element).__name__}"
            )
        self._collection.append(element)
    
    def extend(self, *elements):
        for element in elements:
            if not isinstance(element, self.CLASS_TYPE):
                raise TypeError(
                    f"{self.__class__.__name__} only accepts "
                    f"{self.CLASS_TYPE.__name__} objects, got "
                    f"{type(element).__name__}"
                )
        self._collection.extend(elements)
    
    def __iter__(self):
        return iter(self._collection)
    
    def __repr__(self) -> str:
        return f"{self._collection}"
    

class FluSegmentCollection(Collection):

    CLASS_TYPE = FluSegment

    def return_genomes(self):
        genomes, _ = self._group_genomes(skip_invalid=False)
        return genomes

    def return_genomes_with_errors(self):
        return self._group_genomes(skip_invalid=True)

    def _group_genomes(self, skip_invalid):
        return_dict = defaultdict(list)
        for segment in self._collection:
            return_dict[segment.id].append(segment)

        return_collection = FluGenomeCollection()
        errors = []
        for sample_id in sorted(return_dict):
            try:
                genome = FluGenome(*return_dict[sample_id])
            except ValueError as error:
                if not skip_invalid:
                    raise
                errors.append(f"Sample {sample_id!r}: {error}")
                continue
            return_collection.append(genome)
        if skip_invalid:
            return return_collection, errors
        return return_collection, []
    
    @classmethod
    def from_fasta(cls, fasta):
        records = FastaFile(fasta).read()
        if not records:
            raise ValueError(f"FASTA file {fasta!r} contains no records")
        
        instance = cls()
        for record in records:
            try:
                segment = FluSegment.from_record(record)
            except ValueError as error:
                raise ValueError(
                    f"Invalid record in FASTA file {fasta!r}: {error}"
                ) from error
            instance.append(segment)
        
        return instance
    
    @classmethod
    def from_list_files(cls, fasta_list):
        if not fasta_list:
            raise ValueError("At least one FASTA input is required")
        ins_global = cls()
        for fasta in fasta_list:
            ins = cls.from_fasta(fasta)
            ins_global.extend(*ins)
        
        return ins_global

class FluGenome:

    def __init__(self, *segments) -> None:
        if not segments:
            raise ValueError("FluGenome requires at least one segment")
        self._segments = FluSegmentCollection(*segments)
        self._validate_input()
        self._get_id()
        self._get_type()
        self._index_segments()
        self._get_subtype()

    def _validate_input(self):
        self._validate_id()
        self._validate_type()
        self._validate_unique_segments()

    def _get_id(self):
        ids = {segment.id for segment in self._segments}
        self.id = next(iter(ids))

    def _get_type(self):
        types = {segment.type for segment in self._segments}
        self.type = next(iter(types))
    
    def _get_subtype(self):
        ha = self.segments.get(constants.HA)
        na = self.segments.get(constants.NA)
        if (
            self.type == constants.A_TYPE
            and ha is not None
            and na is not None
            and ha.segment_type is not None
            and na.segment_type is not None
        ):
            self.subtype = f"{ha.segment_type}{na.segment_type}"
            return
        self.subtype = None

    def _get_segment_type(self, segment):
        if not self._check_if_segment(segment):
            return None
        return self.segments[segment].segment_type

    def _check_if_segment(self, segment):
        return segment in self.segments

    def _validate_id(self):       
        id = {segment.id for segment in self._segments}
        if len(id) != 1:
            raise ValueError("All segments in a FluGenome must have the same sample ID")
        
    def _validate_type(self):
        type = {segment.type for segment in self._segments}

        if len(type) != 1:
            raise ValueError("All segments in a FluGenome must have the same type")

    def _validate_unique_segments(self):
        seen = set()
        duplicates = set()
        for segment in self._segments:
            if segment.segment in seen:
                duplicates.add(segment.segment)
            seen.add(segment.segment)
        duplicates = sorted(duplicates)
        if duplicates:
            sample_id = self._segments._collection[0].id
            raise ValueError(
                f"Duplicate segments for sample {sample_id!r}: "
                f"{', '.join(duplicates)}"
            )
        
    def __repr__(self) -> str:
        return f'Flu:\n {self.id}-Type-{self.type} {self.subtype} \nSegments:\n{self.segments.values()}'
    
    def _index_segments(self):
        self.segments = {segment.segment: segment for segment in self._segments}

    def get_segments(self):
        segments = [self.segments[name] for name in SEGMENTS if name in self.segments]

        return FluSegmentCollection(*segments)


class FluGenomeSummarizer:
    ID_HEADER = "id"
    TYPE_HEADER = "type"
    SUBTYPE_HEADER = "subtype"
    HEADERS = [ID_HEADER, TYPE_HEADER, SUBTYPE_HEADER]
    SEGMENTS = SEGMENTS
    HEADERS.extend(SEGMENTS)

    @classmethod
    def summary(cls, flu_genome: FluGenome):
        sum_dict = {
            cls.ID_HEADER: flu_genome.id,
            cls.TYPE_HEADER: flu_genome.type,
            cls.SUBTYPE_HEADER: flu_genome.subtype
        }

        for segment in SEGMENTS:
            if segment in flu_genome.segments:
                sum_dict[segment] = flu_genome.segments[segment].length
            else:
                sum_dict[segment] = None
        return sum_dict
    
    @classmethod
    def summary_to_csv(cls, flu_genome, handle):
        """Write one summary row, including its header, to a text handle."""
        writer = csv.DictWriter(handle, fieldnames=cls.HEADERS)
        writer.writeheader()
        writer.writerow(cls.summary(flu_genome))
    
    @classmethod
    def bulk_summarize(cls, flu_genome_collection):
        return_list = []
        for genome in flu_genome_collection:
            summary = cls.summary(genome)
            return_list.append(summary)
        return return_list
    @classmethod
    def bulk_summary_to_csv(cls, flu_genome_collection, handle):
        """Write summaries with one header row to a text handle."""
        writer = csv.DictWriter(handle, fieldnames=cls.HEADERS)
        writer.writeheader()
        writer.writerows(cls.bulk_summarize(flu_genome_collection))


class FluGenomeCollection(Collection):
    CLASS_TYPE = FluGenome

    def to_id_dict(self) -> dict:

        return_dict = {}
        for genome in sorted(self._collection, key=lambda item: item.id):
            if genome.id in return_dict:
                raise ValueError(f"Duplicate genome sample ID {genome.id!r}")
            segments = genome.get_segments()
            return_dict[genome.id] = segments
        return return_dict

    def to_segment_dict(self):
        return_dict = {segment: FluSegmentCollection() for segment in SEGMENTS}

        seen_ids = set()
        for genome in sorted(self._collection, key=lambda item: item.id):
            if genome.id in seen_ids:
                raise ValueError(f"Duplicate genome sample ID {genome.id!r}")
            seen_ids.add(genome.id)
            for segment_name in SEGMENTS:
                segment = genome.segments.get(segment_name)
                if segment is not None:
                    return_dict[segment_name].append(segment)
        return return_dict

    def to_segment_subtype_dict(self):
        grouped = defaultdict(FluSegmentCollection)
        by_id = defaultdict(list)
        for genome in self._collection:
            by_id[genome.id].append(genome)

        errors = []
        for sample_id in sorted(by_id):
            genomes = by_id[sample_id]
            if len(genomes) != 1:
                errors.append(
                    f"Sample {sample_id!r}: duplicate genome records prevent grouping"
                )
                continue
            genome = genomes[0]
            if genome.subtype is None:
                errors.append(
                    f"Sample {genome.id!r}: cannot group segments by subtype; "
                    "complete HA/NA subtype is unavailable"
                )
                continue
            for segment_name in SEGMENTS:
                segment = genome.segments.get(segment_name)
                if segment is not None:
                    key = f"{segment_name}_{genome.subtype}"
                    grouped[key].append(segment)
        return {key: grouped[key] for key in sorted(grouped)}, errors


class FluGenomeRecordCreator:
    @staticmethod
    def create_record(segment_collection):
        records = []
        for segment in segment_collection:
            id = f"{segment.id}_{segment.type}_{segment.segment}"
            if segment.segment_type:
                id = f"{id}_{segment.segment_type}"
            record = FastaRecord(id=id, sequence=str(segment.sequence))
            records.append(record)
        return records
    
    @staticmethod
    def create_record_dict(segment_dict):
        record_dict = {}
        for key, value in segment_dict.items():
            records = FluGenomeRecordCreator.create_record(value)
            record_dict[key] = records
        return record_dict

class FastaFileWriter:
    def write(self, records, dest_file):
        try:
            FastaFile(dest_file).write(records)
        except FileExistsError as error:
            raise FileExistsError(
                f"Refusing to overwrite FASTA file {dest_file!r}"
            ) from error

class FluGenomeFileWriter:
    def __init__(self, file_writer):
        self.file_writer = file_writer

    def write_fasta_from_dict(self, segment_dict, out_dir=""):
        grouped_segments = self._validate_groups(segment_dict)
        record_dict = FluGenomeRecordCreator.create_record_dict(grouped_segments)
        records_to_write = [
            (key, value) for key, value in record_dict.items() if value
        ]
        if not records_to_write:
            raise ValueError("No FASTA records are available to export")

        out_dir = os.fspath(out_dir) if out_dir else os.curdir
        os.makedirs(out_dir, exist_ok=True)
        destinations = self._plan_destinations(records_to_write, out_dir)
        self._write_records(records_to_write, destinations)

    def _write_records(self, records_to_write, destinations):
        for (key, records), dest_file in zip(records_to_write, destinations):
            try:
                self.file_writer.write(records, dest_file)
            except (OSError, ValueError) as error:
                raise type(error)(
                    f"Failed to write FASTA group {key!r} to {dest_file!r}: {error}"
                ) from error

    def _validate_groups(self, segment_dict):
        grouped_segments = {}
        for key, segments in segment_dict.items():
            if (
                not isinstance(key, str)
                or not key
                or key in (".", "..")
                or "/" in key
                or "\\" in key
                or "\0" in key
                or os.path.splitdrive(key)[0]
            ):
                raise ValueError(f"Invalid FASTA output name: {key!r}")
            segment_list = list(segments)
            if any(not isinstance(segment, FluSegment) for segment in segment_list):
                raise TypeError(f"Output group {key!r} contains a non-FluSegment value")
            segment_subtype = None
            if "_" in key:
                candidate_segment, candidate_subtype = key.rsplit("_", 1)
                if (
                    candidate_segment in SEGMENTS
                    and re.fullmatch(r"H\d+N\d+", candidate_subtype)
                ):
                    segment_subtype = (candidate_segment, candidate_subtype)
            is_segment_group = key in SEGMENTS and all(
                segment.segment == key for segment in segment_list
            )
            is_sample_group = all(segment.id == key for segment in segment_list)
            is_segment_subtype_group = bool(segment_subtype) and all(
                self._matches_segment_subtype_group(segment, segment_subtype)
                for segment in segment_list
            )
            if segment_list and not (
                is_segment_group or is_sample_group or is_segment_subtype_group
            ):
                raise ValueError(f"Output group {key!r} mixes samples or segments")
            sample_segments = [(segment.id, segment.segment) for segment in segment_list]
            if len(set(sample_segments)) != len(sample_segments):
                raise ValueError(f"Output group {key!r} contains duplicate segments")
            grouped_segments[key] = segment_list
        return grouped_segments

    @staticmethod
    def _plan_destinations(records_to_write, out_dir):
        destinations = [
            os.path.join(out_dir, f"{key}{constants.FASTA_EXT}")
            for key, _ in records_to_write
        ]
        normalized_destinations = [
            os.path.normcase(os.path.abspath(path)) for path in destinations
        ]
        if len(set(normalized_destinations)) != len(normalized_destinations):
            raise ValueError("FASTA output names resolve to colliding paths")
        existing = [path for path in destinations if os.path.lexists(path)]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite FASTA output(s): " + ", ".join(existing)
            )
        return destinations

    @staticmethod
    def _matches_segment_subtype_group(segment, segment_subtype):
        segment_name, subtype = segment_subtype
        if segment.segment != segment_name or segment.type != constants.A_TYPE:
            return False
        if segment_name == constants.HA:
            expected_segment_type = re.match(r"H\d+", subtype).group(0)
            return segment.segment_type == expected_segment_type
        if segment_name == constants.NA:
            expected_segment_type = re.search(r"N\d+$", subtype).group(0)
            return segment.segment_type == expected_segment_type
        return True

def add_arguments(parser):
    parser.add_argument(
        "-f", "--files", help="FASTA input files", nargs="+", required=True
    )
    parser.add_argument("-o", "--out-dir", "--out_dir", dest="out_dir", default=".")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["samples", "segments"],
        required=True,
        help=(
            "Export by sample, or by segment and complete HXNX subtype "
            "(for example, HA_H3N2)"
        ),
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Write summary.csv to the output directory",
    )
    return parser


def run(args):
    try:
        collection = FluSegmentCollection.from_list_files(args.files)
    except OSError as error:
        raise ValueError(f"Cannot read FASTA input: {error}") from error
    genome_collection, errors = collection.return_genomes_with_errors()

    if args.mode == "samples":
        segments = genome_collection.to_id_dict()
    else:
        segments, subtype_errors = genome_collection.to_segment_subtype_dict()
        errors.extend(subtype_errors)

    file_writer = FastaFileWriter()
    flu_writer = FluGenomeFileWriter(file_writer)
    for error in errors:
        print(f"irmagic: warning: {error}", file=sys.stderr)

    summary_path = None
    out_dir = os.fspath(args.out_dir or os.curdir)
    if args.summary:
        summary_path = os.path.join(out_dir, "summary.csv")
        if os.path.lexists(summary_path):
            raise FileExistsError(f"Refusing to overwrite summary file {summary_path!r}")

    if segments:
        flu_writer.write_fasta_from_dict(segments, out_dir)
    if summary_path is not None:
        os.makedirs(out_dir, exist_ok=True)
        try:
            write_new_file(
                summary_path,
                lambda handle: FluGenomeSummarizer.bulk_summary_to_csv(
                    genome_collection, handle
                ),
                newline="",
            )
        except OSError as error:
            raise OSError(
                f"Failed to write summary file {summary_path!r}: {error}"
            ) from error
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Process influenza FASTA files")
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
