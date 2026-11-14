import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from irma_magic.cli import main
from irma_magic.fasta import FastaFile


class CliTests(unittest.TestCase):
    def test_missing_subcommand_exits_with_argument_error(self):
        stderr = StringIO()
        with patch.object(sys, "argv", ["irmagic"]), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn("command", stderr.getvalue())

    def test_root_and_bulker_help_are_available(self):
        for argv in (
            ["irmagic", "--help"],
            ["irmagic", "bulker", "--help"],
            ["irmagic", "renamer", "--help"],
            ["irmagic", "flu", "--help"],
        ):
            with self.subTest(argv=argv):
                stdout = StringIO()
                with patch.object(sys, "argv", list(argv)), redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as error:
                        main()
                self.assertEqual(error.exception.code, 0)
                self.assertIn("usage:", stdout.getvalue())
                if argv == ["irmagic", "--help"]:
                    for command in ("bulker", "renamer", "flu"):
                        self.assertIn(command, stdout.getvalue())

    def test_bulker_accepts_irma_command_after_subcommand(self):
        with tempfile.TemporaryDirectory() as temporary:
            fastq = Path(temporary) / "sample.fastq"
            fastq.write_text("synthetic read fixture", encoding="utf-8")
            argv = [
                "irmagic", "bulker", "--files", str(fastq), "--module", "MODULE",
                "--irma_cmd", "IRMA-MOCK",
            ]
            with patch.object(sys, "argv", argv), patch(
                "irma_magic.bulk.subprocess.run"
            ) as run:
                self.assertEqual(main(), 0)
            self.assertEqual(run.call_args.args[0][0], "IRMA-MOCK")

    def test_bulker_accepts_hyphenated_options_and_returns_execution_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            forward = root / "sample_F.fastq"
            reverse = root / "sample_R.fastq"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")
            argv = [
                "bulker", "--files", str(forward), str(reverse), "--module", "MODULE",
                "--reads", "paired", "--irma-cmd", "IRMA-MOCK",
                "--forward-pattern", "_F", "--reverse-pattern", "_R",
            ]
            with patch("irma_magic.bulk.subprocess.run") as run:
                self.assertEqual(main(argv), 0)
            self.assertEqual(run.call_args.args[0][0], "IRMA-MOCK")
            self.assertEqual(run.call_args.args[0][2:4], [str(forward), str(reverse)])

            legacy_argv = [
                "bulker", "--files", str(forward), str(reverse), "--module", "MODULE",
                "--reads", "paired", "--irma_cmd", "IRMA-MOCK",
                "--forward_pattern", "_F", "--reverse_pattern", "_R",
            ]
            with patch("irma_magic.bulk.subprocess.run"):
                self.assertEqual(main(legacy_argv), 0)

            stderr = StringIO()
            with patch(
                "irma_magic.bulk.subprocess.run",
                side_effect=subprocess.CalledProcessError(7, "IRMA-MOCK"),
            ), redirect_stderr(stderr):
                self.assertEqual(main(argv), 1)
            self.assertIn("sample", stderr.getvalue())
            self.assertNotIn("usage:", stderr.getvalue())

    def test_invalid_inputs_return_two_without_argparse_io_error_format(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            status = main(["bulker", "--files", "reads.txt", "--module", "MODULE"])
        self.assertEqual(status, 2)
        self.assertIn("irmagic: error:", stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue())

    def test_bulker_missing_fastq_path_returns_two(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            status = main([
                "bulker", "--files", "missing.fastq", "--module", "MODULE",
            ])
        self.assertEqual(status, 2)
        self.assertIn("missing.fastq", stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue())

    def test_renamer_subcommand_copies_files_to_out_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            source = source_dir / "sample.vcf"
            source.write_text("synthetic vcf", encoding="utf-8")
            output = root / "output"
            argv = [
                "irmagic", "renamer", "--dirs", str(source_dir),
                "--types", "vcf", "--out-dir", str(output),
            ]

            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

            self.assertEqual(
                (output / "run_sample.vcf").read_text(encoding="utf-8"),
                "synthetic vcf",
            )

    def test_renamer_legacy_option_alias_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            (source_dir / "sample.vcf").write_text("vcf", encoding="utf-8")
            output = root / "out"
            self.assertEqual(main([
                "renamer", "--dirs", str(source_dir), "--types", "vcf",
                "--out_dir", str(output),
            ]), 0)

        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main([
                "renamer", "--dirs", "missing-dir", "--types", "vcf",
            ]), 2)
        self.assertIn("irmagic: error:", stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            (source_dir / "sample.vcf").write_text("vcf", encoding="utf-8")
            output = root / "out"
            output.mkdir()
            (output / "run_sample.vcf").write_text("keep", encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                status = main([
                    "renamer", "--dirs", str(source_dir), "--types", "vcf",
                    "--out-dir", str(output),
                ])
            self.assertEqual(status, 1)
            self.assertIn("irmagic: error:", stderr.getvalue())
            self.assertNotIn("usage:", stderr.getvalue())

    def test_flu_invalid_input_returns_two(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "bad.fasta"
            source.write_text(">not-an-influenza-id\nACGT\n", encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                status = main([
                    "flu", "--files", str(source), "--mode", "samples",
                ])
        self.assertEqual(status, 2)
        self.assertIn("irmagic: error:", stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue())

    def test_flu_subcommand_writes_fasta_and_csv_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.fasta"
            source.write_text(
                ">sample_A_HA_H3\nACGT\n>sample_A_NA_N2\nTGCA\n",
                encoding="utf-8",
            )
            output = root / "output"
            argv = [
                "irmagic", "flu", "--files", str(source),
                "--mode", "samples", "--out_dir", str(output), "--summary",
            ]

            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

            self.assertEqual(
                [record.id for record in FastaFile(output / "sample.fasta").read()],
                ["sample_A_HA_H3", "sample_A_NA_N2"],
            )
            summary = (output / "summary.csv").read_text(encoding="utf-8")
            self.assertIn("id,type,subtype", summary)
            self.assertIn("sample,A,H3N2", summary)


if __name__ == "__main__":
    unittest.main()
