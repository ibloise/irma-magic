"""Baseline regression cases for H0; expected failures capture existing defects."""

import unittest
from unittest.mock import patch

from irma_magic.bulk import IrmaBulk
from irma_magic.files import FastqCollection, FastqFile


class FastqBaselineTests(unittest.TestCase):
    def test_supported_fastq_suffixes(self):
        for name in ("reads.fastq", "reads.fq", "reads.fastq.gz", "reads.fq.gz"):
            with self.subTest(name=name):
                self.assertIsInstance(FastqFile(name), FastqFile)

    @unittest.expectedFailure
    def test_rejects_non_fastq_gzip(self):
        with self.assertRaises(ValueError):
            FastqFile("reads.txt.gz")

    @unittest.expectedFailure
    def test_fastq_file_exposes_full_name(self):
        self.assertEqual(FastqFile("/data/reads.fastq").full_name,
                         "/data/reads.fastq")

    @unittest.expectedFailure
    def test_pairs_by_sample_not_list_position(self):
        collection = FastqCollection.from_list(
            files=["b_R2.fastq", "a_R1.fastq", "a_R2.fastq", "b_R1.fastq"],
            paired=True,
        )
        pairs = list(collection.iter_files())
        self.assertEqual(
            [(pair.files[0].name[0], pair.files[1].name[0]) for pair in pairs],
            [("a", "a"), ("b", "b")],
        )

    @unittest.expectedFailure
    def test_orphan_read_is_not_silently_dropped(self):
        collection = FastqCollection.from_list(
            files=["a_R1.fastq", "a_R2.fastq", "orphan_R1.fastq"],
            paired=True,
        )
        self.assertEqual(len(list(collection.iter_files())), 2)

    @unittest.expectedFailure
    def test_transform_file_runs_once_per_input(self):
        collection = FastqCollection()
        transform = collection._transform_file
        with patch.object(collection, "_transform_file", wraps=transform) as mocked:
            collection.append_files(["reads.fastq"], paired=False)
        self.assertEqual(mocked.call_count, 1)


class BulkBaselineTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_command_preserves_source_path_with_spaces(self):
        bulk = IrmaBulk("module", [], "single")
        command = bulk._build_cmd([FastqFile("/data/run 1/reads.fastq")])
        self.assertIn("/data/run 1/reads.fastq", command)

    @unittest.expectedFailure
    def test_nonzero_irma_exit_is_reported(self):
        bulk = IrmaBulk("module", [], "single")
        bulk._cmd_list = [["IRMA", "module"]]
        with patch("irma_magic.bulk.subprocess.run", return_value=type(
                "Result", (), {"returncode": 2})()):
            with self.assertRaises(Exception):
                bulk.run()


if __name__ == "__main__":
    unittest.main()
