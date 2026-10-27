"""Reject misleading mixtures of saved quality and denominator summaries."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.plot_fastq_qc import load_summary, render, validate_output

ROOT = Path(__file__).resolve().parents[1]


class CycleContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        for name in ("report.json", "cycles.csv"):
            shutil.copyfile(ROOT / "reports/fastq_synthetic" / name, self.path / name)

    def change_cycles(self, change):
        path = self.path / "cycles.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_frozen_public_and_synthetic_denominators(self):
        for folder in ("fastq_synthetic", "fastq_public"):
            report, rows = load_summary(ROOT / "reports" / folder)
            self.assertEqual(len(rows), len(report["samples"]))
        _, rows = load_summary(self.path)
        self.assertEqual(rows["toy_sample_A"][-1]["observed_bases"], 1)

    def test_duplicate_or_missing_cycle_rejected(self):
        self.change_cycles(lambda rows: rows.__setitem__(1, rows[0].copy()))
        with self.assertRaisesRegex(ValueError, "unique and contiguous"):
            load_summary(self.path)

    def test_denominator_mismatch_rejected(self):
        self.change_cycles(lambda rows: rows[0].update(observed_bases="2"))
        with self.assertRaisesRegex(ValueError, "read count"):
            load_summary(self.path)

    def test_nonfinite_quality_rejected(self):
        self.change_cycles(lambda rows: rows[0].update(mean_phred="nan"))
        with self.assertRaisesRegex(ValueError, "finite"):
            load_summary(self.path)

    def test_mixed_report_and_cycle_quality_rejected(self):
        self.change_cycles(lambda rows: rows[0].update(mean_phred="1"))
        with self.assertRaisesRegex(ValueError, "disagrees"):
            load_summary(self.path)

    def test_source_provenance_copy_is_preserved_before_plotting(self):
        output = self.path / "source-copy"
        output.mkdir()
        original = (ROOT / "examples/public/provenance.json").read_bytes()
        (output / "provenance.json").write_bytes(original)
        with patch("scripts.plot_fastq_qc.load_summary", side_effect=AssertionError("must reject before reading")):
            with self.assertRaisesRegex(ValueError, "recognized cycle-context"):
                render(ROOT / "reports/fastq_public", output)
        self.assertEqual((output / "provenance.json").read_bytes(), original)
        self.assertEqual([p.name for p in output.iterdir()], ["provenance.json"])

    def test_source_and_input_report_directories_are_rejected(self):
        inputs = ROOT / "reports/fastq_public"
        for output in (ROOT, ROOT / "examples/public", ROOT / "examples/new",
                       ROOT / "data/new", ROOT / "reports/new", self.path / "nested"):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "outside input"):
                validate_output(self.path if output == self.path / "nested" else inputs, output)

    def test_documented_figure_regeneration_remains_allowed(self):
        for folder in ("fastq_public", "fastq_synthetic"):
            output = ROOT / "docs/figures" / folder
            self.assertEqual(validate_output(ROOT / "reports" / folder, output), output.resolve())

    def test_unidentified_existing_image_is_not_replaced(self):
        output = self.path / "figures"
        output.mkdir()
        (output / "cycle-context.png").write_bytes(b"unrelated image")
        with self.assertRaisesRegex(ValueError, "recognized cycle-context"):
            validate_output(ROOT / "reports/fastq_public", output)
        self.assertEqual((output / "cycle-context.png").read_bytes(), b"unrelated image")

    def test_output_parent_and_file_link_guards_run_before_publication(self):
        output = self.path / "figures"
        for linked in (output, self.path, output / "provenance.json"):
            with self.subTest(linked=linked), patch("scripts.plot_fastq_qc._is_link", side_effect=lambda p: p == linked):
                with self.assertRaisesRegex(ValueError, "links|symlinks"):
                    validate_output(ROOT / "reports/fastq_public", output)


if __name__ == "__main__":
    unittest.main()
