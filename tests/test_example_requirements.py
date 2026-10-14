"""Unit tests for scripts/example_requirements.py."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import example_requirements as reqs  # noqa: E402


class RequirementNamesTests(unittest.TestCase):
    def test_requirement_names_parses_comments_options_specifiers(self):
        content = (
            "# top\n"
            "pytest>=8  # c\n"
            "\n"
            "-r base.txt\n"
            "sqlalchemy-cubrid[pycubrid]==1\n"
            "  Foo_bar.baz ; python_version<'3.12'\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.txt"
            path.write_text(content, encoding="utf-8")
            self.assertEqual(
                reqs.requirement_names(path),
                ["pytest", "sqlalchemy-cubrid", "Foo_bar.baz"],
            )


class MissingDistributionsTests(unittest.TestCase):
    def test_missing_distributions_reports_uninstalled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "demo"
            expected = example / "expected"
            expected.mkdir(parents=True)
            req_file = example / "requirements.txt"
            req_file.write_text("pytest\nmissingpkg\n", encoding="utf-8")

            def fake_distribution(name):
                if name == "pytest":
                    return mock.Mock()
                raise reqs.metadata.PackageNotFoundError(name)

            with mock.patch.object(reqs.metadata, "distribution", side_effect=fake_distribution):
                missing = reqs.missing_distributions([root])
                self.assertEqual(missing, [f"missingpkg ({req_file.as_posix()})"])


class MainCheckTests(unittest.TestCase):
    def test_main_check_fails_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "demo"
            expected = example / "expected"
            expected.mkdir(parents=True)
            (example / "requirements.txt").write_text("notinstalled\n", encoding="utf-8")

            with mock.patch.object(
                reqs.metadata, "distribution", side_effect=reqs.metadata.PackageNotFoundError
            ):
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    code = reqs.main(["--check", str(root)])
                self.assertEqual(code, 1)
                self.assertIn("Missing example dependencies: run `make deps` first.", stderr.getvalue())

    def test_main_check_succeeds_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            example = root / "examples" / "demo"
            expected = example / "expected"
            expected.mkdir(parents=True)
            (example / "requirements.txt").write_text("pytest\n", encoding="utf-8")

            with mock.patch.object(reqs.metadata, "distribution", return_value=mock.Mock()):
                code = reqs.main(["--check", str(root)])
                self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
