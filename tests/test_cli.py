import unittest
from argparse import Namespace
from io import StringIO
from contextlib import redirect_stdout
from presentation_validator.cli import run_validate_dir

class TestCLI(unittest.TestCase):

    def test_v2_dir(self):
        args = Namespace(directory="fixtures/2", version="2.1", extension=".json")

        output = StringIO()
        with redirect_stdout(output):
            rc = run_validate_dir(args)

        text = output.getvalue()

        self.assertEqual(rc, 0)
        self.assertIn("Found 1 files with extension '.json'", text)
        self.assertIn("Passed: 1", text)
        self.assertIn("Failed: 0", text)

    def test_v3_dir(self):
        args = Namespace(directory="fixtures/3", version="3.0", extension=".json")

        output = StringIO()
        with redirect_stdout(output):
            rc = run_validate_dir(args)

        text = output.getvalue()

        print (text)

        self.assertEqual(rc, 1)
        self.assertIn("Found 32 files with extension '.json'", text)
        self.assertIn("Passed: 23", text)
        self.assertIn("Failed: 9", text)