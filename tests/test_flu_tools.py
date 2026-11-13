import os
import csv
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from irma_magic import constants
from irma_magic.fasta import FastaFile, FastaRecord
from irma_magic.flu_tools import (
    FluGenome,
    FluGenomeCollection,
    FluGenomeFileWriter,
    FluGenomeSummarizer,
    FluSegment,
    FluSegmentCollection,
    FastaFileWriter,
    SEGMENTS,
)


def make_segment(sample_id, segment, sequence, flu_type="A", segment_type=None):
    return FluSegment(sample_id, segment, sequence, flu_type, segment_type)


class FluSegmentTests(unittest.TestCase):
    def test_parses_strict_ids_with_underscored_sample_names(self):
        cases = (
            ("sample_with_under_A_HA_H1", ("sample_with_under", "A", "HA", "H1")),
            ("sample_with_under_A_NA_N2", ("sample_with_under", "A", "NA", "N2")),
            ("sample_B_MP", ("sample", "B", constants.M, None)),
        )
        for record_id, expected in cases:
            with self.subTest(record_id=record_id):
                self.assertEqual(FluSegment.parse_id(record_id), expected)

    def test_rejects_invalid_or_ambiguous_ids_and_subtypes(self):
        invalid_ids = (
            "sample_C_HA_H1",
            "sample_A_M",
            "sample_A_HA_H1_extra",
            "sample_A_HA_N1",
            "sample_B_HA_H1",
            "_A_HA_H1",
            "sample_A_PB2_H1",
            "sample name_A_NP",
        )
        for record_id in invalid_ids:
            with self.subTest(record_id=record_id):
                with self.assertRaises(ValueError):
                    FluSegment.parse_id(record_id)

    def test_rejects_empty_sequence_and_invalid_direct_segments(self):
        with self.assertRaisesRegex(ValueError, "sequence cannot be empty"):
            make_segment("sample", constants.NP, "")
        with self.assertRaisesRegex(ValueError, "Unsupported influenza segment"):
            make_segment("sample", "M", "ACGT")

    def test_reads_single_record_and_rejects_empty_or_multiple_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segment.fasta"
            path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "contains no records"):
                FluSegment.read_file(str(path))

            path.write_text(
                ">sample_with_under_A_HA_H1\nACGT\n", encoding="utf-8"
            )
            segment = FluSegment.read_file(str(path))
            self.assertEqual((segment.id, segment.segment, segment.sequence),
                             ("sample_with_under", constants.HA, "ACGT"))

            path.write_text(
                ">sample_A_HA_H1\nACGT\n>sample_A_NA_N1\nTGCA\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Only single-fasta"):
                FluSegment.read_file(str(path))


class FluGenomeTests(unittest.TestCase):
    def test_a_subtypes_h1n1_and_h3n2(self):
        h1n1 = FluGenome(
            FluSegment.from_record(FastaRecord("sample_h1_A_HA_H1", "AAAA")),
            FluSegment.from_record(FastaRecord("sample_h1_A_NA_N1", "CCCC")),
        )
        h3n2 = FluGenome(
            FluSegment.from_record(FastaRecord("sample_h3_A_HA_H3", "GGGG")),
            FluSegment.from_record(FastaRecord("sample_h3_A_NA_N2", "TTTT")),
        )
        self.assertEqual(h1n1.subtype, "H1N1")
        self.assertEqual(h3n2.subtype, "H3N2")

    def test_b_type_and_incomplete_or_unknown_subtypes_are_none(self):
        flu_b = FluGenome(
            FluSegment.from_record(FastaRecord("flu_b_B_HA", "AAAA")),
            FluSegment.from_record(FastaRecord("flu_b_B_NA", "CCCC")),
        )
        missing_na = FluGenome(
            make_segment("missing_na", constants.HA, "AAAA", segment_type="H1")
        )
        unknown_na = FluGenome(
            make_segment("unknown", constants.HA, "AAAA", segment_type="H1"),
            make_segment("unknown", constants.NA, "CCCC"),
        )
        self.assertIsNone(flu_b.subtype)
        self.assertIsNone(missing_na.subtype)
        self.assertIsNone(unknown_na.subtype)

    def test_empty_genome_and_duplicate_segments_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one segment"):
            FluGenome()
        with self.assertRaisesRegex(ValueError, "Duplicate segments.*HA"):
            FluGenome(
                make_segment("sample", constants.HA, "AAAA", segment_type="H1"),
                make_segment("sample", constants.HA, "CCCC", segment_type="H3"),
            )

    def test_mixed_sample_ids_and_types_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "same sample ID"):
            FluGenome(
                make_segment("one", constants.HA, "AAAA", segment_type="H1"),
                make_segment("two", constants.NA, "CCCC", segment_type="N1"),
            )
        with self.assertRaisesRegex(ValueError, "same type"):
            FluGenome(
                make_segment("sample", constants.HA, "AAAA", segment_type="H1"),
                make_segment("sample", constants.NA, "CCCC", flu_type="B"),
            )

    def test_summary_keeps_unknown_subtype_explicit(self):
        genome = FluGenome(make_segment("sample", constants.NP, "ACGT"))
        summary = FluGenomeSummarizer.summary(genome)
        self.assertIsNone(summary["subtype"])
        self.assertEqual(summary[constants.NP], 4)
        self.assertIsNone(summary[constants.HA])

    def test_summary_writes_standard_csv(self):
        genome = FluGenome(
            make_segment("sample", constants.NP, "ACGT"),
            make_segment("sample", constants.HA, "AAAA", segment_type="H1"),
            make_segment("sample", constants.NA, "CCCC", segment_type="N1"),
        )
        output = StringIO(newline="")
        FluGenomeSummarizer.summary_to_csv(genome, output)
        rows = list(csv.DictReader(StringIO(output.getvalue())))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "sample")
        self.assertEqual(rows[0]["subtype"], "H1N1")
        self.assertEqual(rows[0][constants.NP], "4")
        self.assertEqual(rows[0][constants.PB2], "")

    def test_bulk_summary_writes_header_once_and_all_rows(self):
        genomes = FluGenomeCollection(
            FluGenome(make_segment("sample_b", constants.NP, "AC")),
            FluGenome(make_segment("sample_a", constants.NP, "ACGT")),
        )
        output = StringIO(newline="")
        FluGenomeSummarizer.bulk_summary_to_csv(genomes, output)
        rows = list(csv.DictReader(StringIO(output.getvalue())))

        self.assertEqual([row["id"] for row in rows], ["sample_b", "sample_a"])
        self.assertEqual([row[constants.NP] for row in rows], ["2", "4"])

    def test_collections_reject_wrong_types_and_order_samples(self):
        collection = FluSegmentCollection(
            make_segment("z_sample", constants.NP, "AAAA"),
            make_segment("a_sample", constants.PA, "CCCC"),
        )
        with self.assertRaises(TypeError):
            collection.append("not a segment")

        genomes = collection.return_genomes()
        by_sample = genomes.to_id_dict()
        self.assertEqual(list(by_sample), ["a_sample", "z_sample"])

    def test_to_id_dict_rejects_duplicate_genomes(self):
        genome = FluGenome(make_segment("sample", constants.NP, "ACGT"))
        with self.assertRaisesRegex(ValueError, "Duplicate genome sample ID"):
            FluGenomeCollection(genome, genome).to_id_dict()
        with self.assertRaisesRegex(ValueError, "Duplicate genome sample ID"):
            FluGenomeCollection(genome, genome).to_segment_dict()

    def test_to_segment_dict_preserves_segments_and_orders_samples(self):
        collection = FluSegmentCollection(
            make_segment("z_sample", constants.HA, "AAAA", segment_type="H3"),
            make_segment("a_sample", constants.HA, "CCCC", segment_type="H1"),
            make_segment("a_sample", constants.NA, "GGGG", segment_type="N1"),
        )
        segment_dict = collection.return_genomes().to_segment_dict()
        self.assertEqual(
            [(segment.id, segment.sequence) for segment in segment_dict[constants.HA]],
            [("a_sample", "CCCC"), ("z_sample", "AAAA")],
        )
        self.assertEqual([segment.id for segment in segment_dict[constants.NA]],
                         ["a_sample"])
        self.assertEqual(set(segment_dict), set(SEGMENTS))


class FluFastaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.segments = FluSegmentCollection(
            make_segment("z_sample", constants.NP, "AACCGG"),
            make_segment("z_sample", constants.M, "GGTACC"),
            make_segment("z_sample", constants.HA, "GGTA", segment_type="H3"),
            make_segment("z_sample", constants.NA, "CCGT", segment_type="N2"),
            make_segment("a_sample", constants.HA, "ACTG", segment_type="H1"),
            make_segment("a_sample", constants.NA, "GGTA", segment_type="N1"),
            make_segment("a_sample", constants.NP, "CCAA"),
            make_segment("a_sample", constants.M, "TTGG"),
        )
        self.genomes = self.segments.return_genomes()
        self.writer = FluGenomeFileWriter(FastaFileWriter())

    def test_from_fasta_reads_multiple_underscored_ids_and_rejects_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.fasta"
            path.write_text(
                ">sample_with_under_A_HA_H1\nACGT\n"
                ">sample_with_under_A_NA_N1\nTGCA\n",
                encoding="utf-8",
            )
            segments = FluSegmentCollection.from_fasta(str(path))
            self.assertEqual([segment.id for segment in segments],
                             ["sample_with_under", "sample_with_under"])
            self.assertEqual(segments.return_genomes()._collection[0].subtype, "H1N1")

            path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "contains no records"):
                FluSegmentCollection.from_fasta(str(path))

            path.write_text("ACGT\n>sample_A_NP\nTGCA\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "before the first header"):
                FluSegmentCollection.from_fasta(str(path))

    def test_from_list_files_rejects_empty_input(self):
        with self.assertRaisesRegex(ValueError, "At least one FASTA input"):
            FluSegmentCollection.from_list_files([])

    def test_duplicate_fasta_segment_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicates.fasta"
            path.write_text(
                ">sample_A_HA_H1\nAAAA\n>sample_A_HA_H3\nCCCC\n",
                encoding="utf-8",
            )
            segments = FluSegmentCollection.from_fasta(str(path))
            with self.assertRaisesRegex(ValueError, "Duplicate segments.*HA"):
                segments.return_genomes()

    def test_sample_and_segment_exports_are_deterministic_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            sample_dir = Path(directory) / "samples"
            segment_dir = Path(directory) / "segments"
            self.writer.write_fasta_from_dict(self.genomes.to_id_dict(), sample_dir)
            segment_groups, errors = self.genomes.to_segment_subtype_dict()
            self.assertEqual(errors, [])
            self.writer.write_fasta_from_dict(
                segment_groups, segment_dir
            )

            sample_a = FastaFile(str(sample_dir / "a_sample.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in sample_a],
                [
                    ("a_sample_A_NP", "CCAA"),
                    ("a_sample_A_HA_H1", "ACTG"),
                    ("a_sample_A_NA_N1", "GGTA"),
                    ("a_sample_A_MP", "TTGG"),
                ],
            )
            ha_records = FastaFile(str(segment_dir / "HA_H1N1.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in ha_records],
                [("a_sample_A_HA_H1", "ACTG")],
            )
            na_records = FastaFile(str(segment_dir / "NA_H1N1.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in na_records],
                [("a_sample_A_NA_N1", "GGTA")],
            )
            np_records = FastaFile(str(segment_dir / "NP_H1N1.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in np_records],
                [("a_sample_A_NP", "CCAA")],
            )
            mp_records = FastaFile(str(segment_dir / "MP_H3N2.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in mp_records],
                [("z_sample_A_MP", "GGTACC")],
            )
            ha_h3_records = FastaFile(str(segment_dir / "HA_H3N2.fasta")).read()
            na_h3_records = FastaFile(str(segment_dir / "NA_H3N2.fasta")).read()
            mp_h1_records = FastaFile(str(segment_dir / "MP_H1N1.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in ha_h3_records],
                [("z_sample_A_HA_H3", "GGTA")],
            )
            self.assertEqual(
                [(record.id, record.sequence) for record in na_h3_records],
                [("z_sample_A_NA_N2", "CCGT")],
            )
            self.assertEqual(
                [(record.id, record.sequence) for record in mp_h1_records],
                [("a_sample_A_MP", "TTGG")],
            )
            np_h3_records = FastaFile(str(segment_dir / "NP_H3N2.fasta")).read()
            self.assertEqual(
                [(record.id, record.sequence) for record in np_h3_records],
                [("z_sample_A_NP", "AACCGG")],
            )
            self.assertEqual(
                sorted(path.name for path in segment_dir.glob("*.fasta")),
                [
                    "HA_H1N1.fasta",
                    "HA_H3N2.fasta",
                    "MP_H1N1.fasta",
                    "MP_H3N2.fasta",
                    "NA_H1N1.fasta",
                    "NA_H3N2.fasta",
                    "NP_H1N1.fasta",
                    "NP_H3N2.fasta",
                ],
            )
            self.assertFalse((segment_dir / "PB2_H1N1.fasta").exists())

            reparsed = FluSegmentCollection.from_fasta(
                str(segment_dir / "NP_H1N1.fasta")
            )
            self.assertEqual([(segment.id, segment.sequence) for segment in reparsed],
                             [("a_sample", "CCAA")])

    def test_subtype_grouping_skips_and_reports_unknown_or_incomplete_samples(self):
        complete = FluGenome(
            make_segment("complete", constants.HA, "AAAA", segment_type="H1"),
            make_segment("complete", constants.NA, "CCCC", segment_type="N1"),
            make_segment("complete", constants.M, "GGGG"),
        )
        incomplete = FluGenome(make_segment("incomplete", constants.M, "TTTT"))
        flu_b = FluGenome(
            make_segment("flu_b", constants.M, "CCCC", flu_type="B")
        )
        grouped, errors = FluGenomeCollection(complete, incomplete, flu_b).to_segment_subtype_dict()
        self.assertEqual(
            sorted(grouped),
            ["HA_H1N1", "MP_H1N1", "NA_H1N1"],
        )
        self.assertEqual(len(errors), 2)
        self.assertIn("flu_b", errors[0])
        self.assertIn("incomplete", errors[1])

        with tempfile.TemporaryDirectory() as directory:
            self.writer.write_fasta_from_dict(
                FluGenomeCollection(incomplete).to_id_dict(), directory
            )
            self.assertEqual(
                FastaFile(str(Path(directory) / "incomplete.fasta")).read()[0].sequence,
                "TTTT",
            )

    def test_existing_output_collision_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "already-there"
            output_dir.mkdir()
            sentinel = output_dir / "NP_H1N1.fasta"
            sentinel.write_text("keep this\n", encoding="utf-8")
            segment_groups, errors = self.genomes.to_segment_subtype_dict()
            self.assertEqual(errors, [])
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                self.writer.write_fasta_from_dict(segment_groups, output_dir)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep this\n")
            self.assertFalse((output_dir / "HA_H1N1.fasta").exists())

    def test_fasta_file_writer_refuses_to_overwrite_direct_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.fasta"
            path.write_text("original\n", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                FastaFileWriter().write([FastaRecord("sample_A_NP", "ACGT")], path)
            self.assertEqual(path.read_text(encoding="utf-8"), "original\n")

    def test_none_output_dir_uses_current_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_directory = os.getcwd()
            try:
                os.chdir(directory)
                self.writer.write_fasta_from_dict(
                    self.genomes.to_id_dict(), out_dir=None
                )
                self.assertTrue(Path("a_sample.fasta").is_file())
            finally:
                os.chdir(previous_directory)

    def test_output_path_traversal_and_mixed_groups_are_rejected(self):
        unsafe_genome = FluGenome(
            make_segment("../escape", constants.NP, "ACGT")
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Invalid FASTA output name"):
                self.writer.write_fasta_from_dict(
                    FluGenomeCollection(unsafe_genome).to_id_dict(), directory
                )

            mixed = {"sample": [
                make_segment("sample", constants.HA, "AAAA", segment_type="H1"),
                make_segment("other", constants.NA, "CCCC", segment_type="N1"),
            ]}
            with self.assertRaisesRegex(ValueError, "mixes samples or segments"):
                self.writer.write_fasta_from_dict(mixed, directory)

    def test_empty_export_fails_without_creating_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "new"
            with self.assertRaisesRegex(ValueError, "No FASTA records"):
                self.writer.write_fasta_from_dict({constants.HA: []}, output_dir)
            self.assertFalse(output_dir.exists())

    def test_cli_requires_mode(self):
        from irma_magic import flu_tools

        with patch("sys.argv", ["flu-tools", "-f", "input.fasta"]):
            with self.assertRaises(SystemExit) as error:
                flu_tools.main()
        self.assertEqual(error.exception.code, 2)

    def test_cli_segments_mode_writes_segment_and_subtype_names(self):
        from irma_magic import flu_tools

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.fasta"
            output = Path(directory) / "results"
            source.write_text(
                ">sample_A_HA_H1\nAAAA\n"
                ">sample_A_NA_N1\nCCCC\n"
                ">sample_A_MP\nGGGG\n",
                encoding="utf-8",
            )
            argv = [
                "flu-tools", "-f", str(source), "-m", "segments",
                "-o", str(output),
            ]
            with patch("sys.argv", argv):
                flu_tools.main()
            self.assertEqual(
                sorted(path.name for path in output.glob("*.fasta")),
                ["HA_H1N1.fasta", "MP_H1N1.fasta", "NA_H1N1.fasta"],
            )

    def test_cli_keeps_processing_when_one_sample_lacks_subtype(self):
        from irma_magic import flu_tools

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.fasta"
            output = Path(directory) / "results"
            source.write_text(
                ">valid_A_HA_H1\nAAAA\n"
                ">valid_A_NA_N1\nCCCC\n"
                ">valid_A_MP\nGGGG\n"
                ">incomplete_A_MP\nTTTT\n",
                encoding="utf-8",
            )
            argv = [
                "flu-tools", "-f", str(source), "-m", "segments",
                "-o", str(output),
            ]
            stderr = StringIO()
            with patch("sys.argv", argv), redirect_stderr(stderr):
                status = flu_tools.main()
            self.assertEqual(status, 1)
            self.assertIn("incomplete", stderr.getvalue())
            self.assertEqual(
                sorted(path.name for path in output.glob("*.fasta")),
                ["HA_H1N1.fasta", "MP_H1N1.fasta", "NA_H1N1.fasta"],
            )
            mp_records = FastaFile(str(output / "MP_H1N1.fasta")).read()
            self.assertEqual([record.id for record in mp_records], ["valid_A_MP"])

    def test_genome_build_errors_are_isolated_per_sample(self):
        segments = FluSegmentCollection(
            make_segment("valid", constants.NP, "AAAA"),
            make_segment("broken", constants.HA, "CCCC", segment_type="H1"),
            make_segment("broken", constants.HA, "GGGG", segment_type="H3"),
        )
        genomes, errors = segments.return_genomes_with_errors()
        self.assertEqual([genome.id for genome in genomes], ["valid"])
        self.assertEqual(len(errors), 1)
        self.assertIn("broken", errors[0])


if __name__ == "__main__":
    unittest.main()
