import tempfile
import unittest
from pathlib import Path

from irma_magic import constants
from irma_magic.fasta import FastaFile
from irma_magic.renamer import FastaRenamer, IrmaDirRenamer, IrmaRenamer


class RenamerTests(unittest.TestCase):
    def test_copies_to_output_directory_and_keeps_multidot_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run one"
            source_dir.mkdir()
            source = source_dir / "sample.v2.bam"
            source.write_bytes(b"bam bytes")
            output = root / "nested" / "output"

            destination = IrmaRenamer(source, output).rename()

            self.assertEqual(Path(destination), output / "run one_sample.v2.bam")
            self.assertEqual(Path(destination).read_bytes(), b"bam bytes")
            self.assertEqual(source.read_bytes(), b"bam bytes")

    def test_copy_refuses_to_overwrite_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            source = source_dir / "sample.vcf"
            source.write_text("source", encoding="utf-8")
            output = root / "out"
            output.mkdir()
            destination = output / "run_sample.vcf"
            destination.write_text("keep", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                IrmaRenamer(source, output).rename()
            self.assertEqual(destination.read_text(encoding="utf-8"), "keep")

    def test_fasta_renames_ids_without_substring_matches_and_keeps_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            source = source_dir / "sample.v2.fasta"
            source.write_text(
                ">prefix_run_sample.v2_extra description\nACGT\n"
                ">run_sample.v2_existing description two\nTGCA\n",
                encoding="utf-8",
            )
            original = FastaFile(source).read()

            destination = FastaRenamer(source, root / "out").rename()
            renamed = FastaFile(destination).read()

            self.assertEqual([record.id for record in renamed], [
                "run_sample.v2_prefix_run_sample.v2_extra",
                "run_sample.v2_existing",
            ])
            self.assertEqual([record.sequence for record in renamed], [
                record.sequence for record in original
            ])
            self.assertEqual([record.description for record in renamed], [
                record.description for record in original
            ])
            self.assertEqual(len(renamed), 2)
            self.assertEqual(len(original), 2)

    def test_batch_preflights_collisions_between_source_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first" / "same"
            second = root / "second" / "same"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "sample.vcf").write_text("one", encoding="utf-8")
            (second / "sample.vcf").write_text("two", encoding="utf-8")
            output = root / "out"
            mapping = {constants.VCF_FILE: IrmaRenamer}
            batch = [
                IrmaDirRenamer(path, [constants.VCF_FILE], mapping, output)
                for path in (first, second)
            ]

            plans = [item for renamer in batch for item in renamer._planned_renamers()]
            with self.assertRaisesRegex(FileExistsError, "same output path"):
                from irma_magic.renamer import _run
                _run(plans, str(output))
            self.assertFalse(output.exists())

    def test_mid_batch_failure_keeps_completed_copy_and_reports_failing_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            (source_dir / "a.vcf").write_text("first", encoding="utf-8")
            (source_dir / "b.vcf").write_text("second", encoding="utf-8")
            output = root / "out"
            mapping = {constants.VCF_FILE: IrmaRenamer}
            batch = IrmaDirRenamer(
                source_dir, [constants.VCF_FILE], mapping, output
            )._planned_renamers()

            def fail():
                raise OSError("simulated copy failure")

            batch[1].rename = fail
            from irma_magic.renamer import _run
            with self.assertRaisesRegex(OSError, "b.vcf"):
                _run(batch, str(output))

            self.assertEqual(
                (output / "run_a.vcf").read_text(encoding="utf-8"), "first"
            )
            self.assertFalse((output / "run_b.vcf").exists())

    def test_fasta_rejects_duplicate_result_ids_without_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            source = source_dir / "sample.fasta"
            source.write_text(">same\nACGT\n>same\nTGCA\n", encoding="utf-8")
            output = root / "out"

            with self.assertRaisesRegex(ValueError, "duplicate FASTA ID"):
                FastaRenamer(source, output).rename()
            self.assertFalse((output / "run_sample.fasta").exists())

    def test_fasta_rejects_empty_input_without_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            source = source_dir / "empty.fasta"
            source.write_text("", encoding="utf-8")
            output = root / "out"

            with self.assertRaisesRegex(ValueError, "contains no records"):
                FastaRenamer(source, output).rename()
            self.assertFalse(output.exists())

    def test_directory_renamer_uses_out_dir_and_filters_extensions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "run"
            source_dir.mkdir()
            (source_dir / "a.vcf").write_text("vcf", encoding="utf-8")
            (source_dir / "ignored.vcf.bak").write_text("backup", encoding="utf-8")
            output = root / "output"
            mapping = {constants.VCF_FILE: IrmaRenamer}

            destinations = IrmaDirRenamer(
                source_dir, [constants.VCF_FILE], mapping, output
            ).rename_files()

            self.assertEqual([Path(path).name for path in destinations], ["run_a.vcf"])
            self.assertEqual((output / "run_a.vcf").read_text(encoding="utf-8"), "vcf")


if __name__ == "__main__":
    unittest.main()
