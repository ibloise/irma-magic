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
                "--types", "vcf", "--out_dir", str(output),
            ]

            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

            self.assertEqual(
                (output / "run_sample.vcf").read_text(encoding="utf-8"),
                "synthetic vcf",
            )

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
