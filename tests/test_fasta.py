import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from irma_magic.fasta import FastaFile, FastaParser, FastaRecord, FastaWriter


class FastaParserTests(unittest.TestCase):
    def test_parses_multiline_records_and_splits_description(self):
        contents = ">sample_A_HA_H1 description text\nAC GT\n\nNn\n>sample_B_NP\nTTAA\n"
        records = list(FastaParser.parse(io.StringIO(contents)))

        self.assertEqual(
            records,
            [
                FastaRecord("sample_A_HA_H1", "ACGTNn", "description text"),
                FastaRecord("sample_B_NP", "TTAA"),
            ],
        )

    def test_preserves_duplicate_ids_for_callers_to_validate(self):
        records = list(FastaParser.parse(io.StringIO(">same\nAC\n>same\nGT\n")))
        self.assertEqual([record.id for record in records], ["same", "same"])

    def test_empty_file_has_no_records(self):
        self.assertEqual(list(FastaParser.parse(io.StringIO("\n  \n"))), [])

    def test_rejects_sequence_before_first_header(self):
        with self.assertRaisesRegex(ValueError, "before the first header"):
            list(FastaParser.parse(io.StringIO("ACGT\n>sample\nTT\n")))

    def test_rejects_empty_header(self):
        with self.assertRaisesRegex(ValueError, "Empty FASTA header"):
            list(FastaParser.parse(io.StringIO(">\nACGT\n")))

    def test_rejects_record_without_sequence(self):
        with self.assertRaisesRegex(ValueError, "empty sequence"):
            list(FastaParser.parse(io.StringIO(">sample description\n>next\nACGT\n")))


class FastaWriterTests(unittest.TestCase):
    def test_wraps_sequence_and_round_trips_ids_and_sequences(self):
        records = [FastaRecord("sample", "ACGTN" * 3, "description")]
        output = io.StringIO()
        FastaWriter(line_width=5).write(records, output)

        self.assertEqual(output.getvalue(), ">sample description\nACGTN\nACGTN\nACGTN\n")
        parsed = list(FastaParser.parse(io.StringIO(output.getvalue())))
        self.assertEqual([(record.id, record.sequence) for record in parsed],
                         [("sample", "ACGTN" * 3)])

    def test_fasta_file_reads_and_writes_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.fasta"
            fasta = FastaFile(str(path))
            fasta.write([FastaRecord("sample", "ACGT")])
            self.assertEqual(fasta.read(), [FastaRecord("sample", "ACGT")])

    def test_failed_write_removes_partial_output_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.fasta"

            def fail_after_partial_write(writer, records, handle):
                handle.write(">sample\nAC")
                raise OSError("simulated disk failure")

            with patch.object(FastaWriter, "write", fail_after_partial_write):
                with self.assertRaisesRegex(OSError, "simulated disk failure"):
                    FastaFile(path).write([FastaRecord("sample", "ACGT")])
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

            path.write_text("original\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                FastaFile(path).write([FastaRecord("replacement", "TGCA")])
            self.assertEqual(path.read_text(encoding="utf-8"), "original\n")

    def test_rejects_nonpositive_line_width(self):
        with self.assertRaises(ValueError):
            FastaWriter(line_width=0)


if __name__ == "__main__":
    unittest.main()
