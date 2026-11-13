import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from irma_magic import cli


class SimulatedIrmaCliTests(unittest.TestCase):
    def test_single_and_paired_batches_reach_simulated_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            single_a = root / "sample-a.fastq"
            single_b = root / "sample-b.fq"
            forward = root / "paired_R1.fastq.gz"
            reverse = root / "paired_R2.fastq.gz"
            for path in (single_a, single_b, forward, reverse):
                path.write_text("synthetic read fixture\n", encoding="utf-8")

            seen_commands = []

            def simulated_run(command, check):
                self.assertTrue(check)
                seen_commands.append(command)

            with patch("irma_magic.bulk.subprocess.run", side_effect=simulated_run):
                with patch(
                    "sys.argv",
                    ["irmagic", "--irma_cmd", "IRMA-MOCK", "bulker", "--files",
                     str(single_a), str(single_b), "--module", "MODULE"],
                ):
                    self.assertEqual(cli.main(), 0)
                with patch(
                    "sys.argv",
                    ["irmagic", "--irma_cmd", "IRMA-MOCK", "bulker", "--files",
                     str(reverse), str(forward), "--module", "MODULE", "--reads", "paired"],
                ):
                    self.assertEqual(cli.main(), 0)

            self.assertEqual(seen_commands, [
                ["IRMA-MOCK", "MODULE", str(single_a), "sample-a"],
                ["IRMA-MOCK", "MODULE", str(single_b), "sample-b"],
                ["IRMA-MOCK", "MODULE", str(forward), str(reverse), "paired"],
            ])

    def test_malformed_paired_batch_fails_before_backend_invocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            orphan = Path(temporary) / "orphan_R1.fastq"
            orphan.write_text("synthetic read fixture\n", encoding="utf-8")
            argv = [
                "irmagic", "bulker", "--files", str(orphan),
                "--module", "MODULE", "--reads", "paired",
            ]
            with patch("sys.argv", argv), patch(
                "irma_magic.bulk.subprocess.run"
            ) as run:
                with self.assertRaises(SystemExit) as error:
                    cli.main()
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
