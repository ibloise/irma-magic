import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from irma_magic.cli import main


class CliTests(unittest.TestCase):
    def test_missing_subcommand_exits_with_argument_error(self):
        stderr = StringIO()
        with patch.object(sys, "argv", ["irmagic"]), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn("command", stderr.getvalue())

    def test_root_and_bulker_help_are_available(self):
        for argv in (["irmagic", "--help"], ["irmagic", "bulker", "--help"]):
            with self.subTest(argv=argv):
                stdout = StringIO()
                with patch.object(sys, "argv", list(argv)), redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as error:
                        main()
                self.assertEqual(error.exception.code, 0)
                self.assertIn("usage:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
