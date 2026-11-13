import subprocess
import sys
import unittest
from pathlib import Path


EFPP = Path(__file__).resolve().parents[1] / "efpp.py"


class TestCLI(unittest.TestCase):

    def test_missing_input_file(self):
        result = subprocess.run(
            [
                sys.executable,
                str(EFPP),
                "__nonexistent_input__.ef",
                "__nonexistent_alias__.list",
            ],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotEqual(result.stderr, "")

    def test_missing_alias_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.ef"
            source.write_text(
                "program test\n"
                "  implicit none\n"
                "end program test\n"
            )

            missing_alias = Path(tmp) / "missing_alias.list"

            result = subprocess.run(
                [
                    sys.executable,
                    str(EFPP),
                    str(source),
                    str(missing_alias),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("efpp: error: file not found:", result.stderr)
            self.assertIn("missing_alias.list", result.stderr)

    def test_invalid_alias_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.ef"
            source.write_text(
                "program test\n"
                "  implicit none\n"
                "end program test\n"
            )

            alias = Path(tmp) / "efpp_alias.list"
            alias.write_text("this is an invalid alias definition\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(EFPP),
                    str(source),
                    str(alias),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("alias", result.stderr.lower())

    def test_incomplete_alias_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.ef"
            source.write_text(
                "program test\n"
                "  implicit none\n"
                "end program test\n"
            )

            alias = Path(tmp) / "efpp_alias.list"
            alias.write_text('"do i bulk" =>\n')

            result = subprocess.run(
                [
                    sys.executable,
                    str(EFPP),
                    str(source),
                    str(alias),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("alias", result.stderr.lower())

    def test_duplicate_alias_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.ef"
            source.write_text(
                "program test\n"
                "  implicit none\n"
                "end program test\n"
            )

            alias = Path(tmp) / "efpp_alias.list"
            alias.write_text(
                '"do i bulk" => "do i = 1, NXPP"\n'
                '"do i bulk" => "do i = 2, NXPP"\n'
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(EFPP),
                    str(source),
                    str(alias),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("duplicate", result.stderr.lower())

if __name__ == "__main__":
    unittest.main()
