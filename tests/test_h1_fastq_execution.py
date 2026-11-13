import subprocess
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch

from irma_magic.bulk import IrmaBulk, IrmaExecutionError
from irma_magic.files import FastqCollection, FastqFile


class FastqFileTests(unittest.TestCase):
    def test_accepts_only_documented_suffixes_and_initializes_metadata(self):
        cases = {
            "reads.fastq": (".fastq", False),
            "reads.fq": (".fq", False),
            "reads.fastq.gz": (".fastq.gz", True),
            "reads.fq.gz": (".fq.gz", True),
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                fastq = FastqFile(filename)
                self.assertEqual((fastq.ext, fastq.compressed), expected)
                self.assertEqual(fastq.full_name, filename)

    def test_preserves_pathlike_and_paths_with_spaces(self):
        fastq = FastqFile("relative run/reads.fq.gz")
        self.assertEqual(fastq.name, "reads.fq.gz")
        self.assertEqual(fastq.full_name, "relative run/reads.fq.gz")
        self.assertTrue(fastq.compressed)

    def test_rejects_unsupported_suffixes(self):
        for filename in ("reads.txt.gz", "reads.fastq.txt", "reads.FASTQ"):
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(ValueError, "must end with"):
                    FastqFile(filename)


class FastqPairingTests(unittest.TestCase):
    def test_rejects_empty_input_list(self):
        with self.assertRaisesRegex(ValueError, "At least one FASTQ input"):
            FastqCollection.from_list(files=[], paired=False)

    def test_pairs_by_sample_in_deterministic_order(self):
        files = [
            "folder with spaces/sample_b_R2.fastq",
            "folder with spaces/sample_a_with_under_R1.fastq",
            "folder with spaces/sample_b_R1.fastq",
            "folder with spaces/sample_a_with_under_R2.fastq",
        ]
        collection = FastqCollection.from_list(files=files, paired=True)
        pairs = list(collection.iter_files())
        self.assertEqual(
            [
                (pair.common_name, pair.files[0].name, pair.files[1].name)
                for pair in pairs
            ],
            [
                ("sample_a_with_under", "sample_a_with_under_R1.fastq",
                 "sample_a_with_under_R2.fastq"),
                ("sample_b", "sample_b_R1.fastq", "sample_b_R2.fastq"),
            ],
        )

    def test_rejects_orphan_forward_or_reverse_reads(self):
        for files, missing in (
            (["sample_R1.fastq"], "missing _R2"),
            (["sample_R2.fastq"], "missing _R1"),
        ):
            with self.subTest(files=files):
                with self.assertRaisesRegex(ValueError, missing):
                    FastqCollection.from_list(files=files, paired=True)

    def test_does_not_pair_same_sample_name_from_different_directories(self):
        with self.assertRaisesRegex(ValueError, "missing _R1|missing _R2"):
            FastqCollection.from_list(
                files=["forward/sample_R1.fastq", "reverse/sample_R2.fastq"],
                paired=True,
            )

    def test_rejects_duplicate_read_for_sample(self):
        files = ["sample_R1.fastq", "sample_R1.fq", "sample_R2.fastq"]
        with self.assertRaisesRegex(ValueError, "duplicate _R1"):
            FastqCollection.from_list(files=files, paired=True)

    def test_rejects_ambiguous_or_missing_markers(self):
        cases = (
            (["sample_R1_R2.fastq"], "Ambiguous read markers"),
            (["sample_R1_lane_R1.fastq"], "repeated read marker"),
            (["sample.fastq"], "contains neither"),
        )
        for files, message in cases:
            with self.subTest(files=files):
                with self.assertRaisesRegex(ValueError, message):
                    FastqCollection.from_list(files=files, paired=True)

    def test_custom_read_markers_are_supported(self):
        collection = FastqCollection.from_list(
            files=["sample_forward.fq", "sample_reverse.fq"],
            paired=True,
            first_pattern="_forward",
            second_pattern="_reverse",
        )
        pair = next(collection.iter_files())
        self.assertEqual(pair.common_name, "sample")

    def test_rejects_duplicate_single_end_output_names(self):
        with self.assertRaisesRegex(ValueError, "output name.*collision"):
            FastqCollection.from_list(
                files=["one/sample.fastq", "two/sample.fq"], paired=False
            )


class IrmaBulkTests(unittest.TestCase):
    def test_single_end_and_paired_commands_use_exact_paths(self):
        single = IrmaBulk(
            "module", ["relative run/single.fastq"], "single", irma_cmd="irma-bin"
        )
        self.assertEqual(
            single._cmd_list,
            [["irma-bin", "module", "relative run/single.fastq", "single"]],
        )

        paired = IrmaBulk(
            "module",
            ["/data/run 1/sample_R2.fq.gz", "/data/run 1/sample_R1.fastq"],
            "paired",
        )
        self.assertEqual(
            paired._cmd_list,
            [["IRMA", "module", "/data/run 1/sample_R1.fastq",
              "/data/run 1/sample_R2.fq.gz", "sample"]],
        )

    def test_successful_process_uses_check_true(self):
        bulk = IrmaBulk("module", ["one.fastq", "two.fq"], "single")
        with patch(
            "irma_magic.bulk.subprocess.run",
            return_value=subprocess.CompletedProcess(["IRMA"], 0),
        ) as run:
            bulk.run()
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(call.kwargs == {"check": True} for call in run.call_args_list))

    def test_nonzero_exit_is_reported_and_stops_the_batch(self):
        bulk = IrmaBulk("module", ["a.fastq", "b.fastq"], "single")
        with patch(
            "irma_magic.bulk.subprocess.run",
            side_effect=subprocess.CalledProcessError(7, "IRMA"),
        ) as run:
            with self.assertRaisesRegex(IrmaExecutionError, "exit code 7"):
                bulk.run()
        self.assertEqual(run.call_count, 1)

    def test_missing_executable_and_permission_error_are_clear(self):
        for failure, message in (
            (FileNotFoundError(), "executable not found"),
            (PermissionError(), "Permission denied"),
        ):
            bulk = IrmaBulk("module", ["sample.fastq"], "single")
            with self.subTest(failure=type(failure).__name__):
                with patch("irma_magic.bulk.subprocess.run", side_effect=failure):
                    with self.assertRaisesRegex(IrmaExecutionError, message):
                        bulk.run()

    def test_add_execution_rejects_output_collision(self):
        bulk = IrmaBulk("module", ["sample.fastq"], "single")
        with self.assertRaisesRegex(ValueError, "output name.*collision"):
            bulk.add_execution(["another/sample.fq"], paired=False)

    def test_cli_returns_failure_status_for_execution_error(self):
        from irma_magic import cli

        stderr = StringIO()
        argv = ["irmagic", "bulker", "-f", "sample.fastq", "-m", "module"]
        with patch("sys.argv", argv), patch.object(
            cli.IrmaBulk, "run", side_effect=IrmaExecutionError("mock failure")
        ), redirect_stderr(stderr):
            status = cli.main()
        self.assertEqual(status, 1)
        self.assertIn("mock failure", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
