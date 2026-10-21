"""Spreadsheet exports escape text while preserving raw QC data and fingerprints."""
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import fastq_qc
import input_fingerprints


class CsvExportTests(unittest.TestCase):
    def test_writer_escapes_formula_text_and_preserves_other_values(self):
        values = [prefix + formula for prefix in ["", " ", "\t", "\r\n", "\v", "\f", "\ufeff", " \t\ufeff"]
                  for formula in ["=1+1", "+1+1", "-1+1", "@SUM(1,2)"]]
        values += ["ordinary", "café", "", "'=1+1", "value,with\nlines"]
        rows = [{"text": value, "negative_integer": -1, "negative_fraction": -0.5,
                 "missing": None, "zero": 0, "flag": False} for value in values]
        original = deepcopy(rows)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            fastq_qc.write_csv(path, rows)
            with path.open(encoding="utf-8", newline="") as stream:
                written = list(csv.DictReader(stream))
        for index, (value, row) in enumerate(zip(values, written)):
            with self.subTest(value=value):
                self.assertEqual(row["text"], "'" + value if index < 32 else value)
                self.assertEqual(row["negative_integer"], "-1")
                self.assertEqual(row["negative_fraction"], "-0.5")
                self.assertEqual(row["missing"], "")
                self.assertEqual(row["zero"], "0")
                self.assertEqual(row["flag"], "False")
        self.assertEqual(rows, original)

    def test_manifest_filenames_escape_only_in_csv_and_keep_input_lock(self):
        names = ["ordinary.fastq", "=1+1", "+1+1", "-1+1", "@SUM(1,2)", " \ufeff=1+1"]
        raw = b"@=1+1\nACGT\n+\nIIII\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in names:
                (root / name).write_bytes(raw)
            manifest = root / "manifest.csv"
            with manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["sample_id", "fastq_path", "quality_encoding"])
                writer.writerows([f"sample{i}", "./" + name, "phred33"] for i, name in enumerate(names))
            manifest_bytes = manifest.read_bytes()
            lock_path = root / "lock.json"
            lock = input_fingerprints.create(manifest, lock_path)
            lock_bytes = lock_path.read_bytes()
            output = root / "out"
            report = fastq_qc.run(manifest, output, "harmless CSV regression", lock_path)
            with (output / "samples.csv").open(encoding="utf-8", newline="") as stream:
                written = list(csv.DictReader(stream))
            self.assertEqual([row["input_name"] for row in written], [names[0]] + ["'" + name for name in names[1:]])
            self.assertEqual([row["input_name"] for row in report["samples"]], names)
            self.assertEqual(json.loads((output / "report.json").read_text(encoding="utf-8")), report)
            self.assertEqual([json.loads(line)["read_id"] for line in (output / "read_metrics.jsonl").read_text(encoding="utf-8").splitlines()], ["=1+1"] * len(names))
            self.assertEqual([row["fastq_path"] for row in lock["files"]], ["./" + name for name in names])
            self.assertTrue(all(row["input_sha256"] == hashlib.sha256(raw).hexdigest() for row in report["samples"]))
            self.assertEqual(manifest.read_bytes(), manifest_bytes)
            self.assertEqual(lock_path.read_bytes(), lock_bytes)
            self.assertTrue(all((root / name).read_bytes() == raw for name in names))


if __name__ == "__main__":
    unittest.main()
