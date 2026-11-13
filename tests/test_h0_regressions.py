"""Regression cases carried forward from the H0 audit."""

import subprocess
import unittest
from unittest.mock import patch

from irma_magic.bulk import IrmaBulk, IrmaExecutionError
from irma_magic.files import FastqCollection, FastqFile


class FastqBaselineTests(unittest.TestCase):
    def test_supported_fastq_suffixes(self):
        for name in ("reads.fastq", "reads.fq", "reads.fastq.gz", "reads.fq.gz"):
            with self.subTest(name=name):
                self.assertIsInstance(FastqFile(name), FastqFile)

    def test_rejects_non_fastq_gzip(self):
        with self.assertRaises(ValueError):
            FastqFile("reads.txt.gz")

    def test_fastq_file_exposes_full_name(self):
        self.assertEqual(FastqFile("/data/reads.fastq").full_name,
                         "/data/reads.fastq")

    def test_pairs_by_sample_not_list_position(self):
        collection = FastqCollection.from_list(
            files=["b_R2.fastq", "a_R1.fastq", "a_R2.fastq", "b_R1.fastq"],
            paired=True,
        )
        pairs = list(collection.iter_files())
        self.assertEqual([(pair.files[0].name, pair.files[1].name) for pair in pairs],
                         [("a_R1.fastq", "a_R2.fastq"),
                          ("b_R1.fastq", "b_R2.fastq")])

    def test_orphan_read_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, "orphan"):
            FastqCollection.from_list(
                files=["a_R1.fastq", "a_R2.fastq", "orphan_R1.fastq"],
                paired=True,
            )

    def test_transform_file_runs_once_per_input(self):
        collection = FastqCollection()
        transform = collection._transform_file
        with patch.object(collection, "_transform_file", wraps=transform) as mocked:
            collection.append_files(["reads.fastq"], paired=False)
        self.assertEqual(mocked.call_count, 1)


class BulkBaselineTests(unittest.TestCase):
    def test_command_preserves_source_path_with_spaces(self):
        bulk = IrmaBulk("module", ["input.fastq"], "single")
        command = bulk._build_cmd([FastqFile("/data/run 1/reads.fastq")])
        self.assertIn("/data/run 1/reads.fastq", command)

    def test_nonzero_irma_exit_is_reported(self):
        bulk = IrmaBulk("module", ["input.fastq"], "single")
        bulk._cmd_list = [["IRMA", "module"]]
        with patch("irma_magic.bulk.subprocess.run", side_effect=subprocess.CalledProcessError(2, "IRMA")):
            with self.assertRaises(IrmaExecutionError):
                bulk.run()


if __name__ == "__main__":
    unittest.main()
