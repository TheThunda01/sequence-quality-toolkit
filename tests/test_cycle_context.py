"""Reject misleading mixtures of saved quality and denominator summaries."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.plot_fastq_qc import load_summary

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


if __name__ == "__main__":
    unittest.main()
