import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

import sequence_qc as qc


class FastaTests(unittest.TestCase):
    def test_wrapped_lowercase_and_descriptions(self):
        records = qc.parse_fasta(io.StringIO("\n>one description\nacgt\nNN\n\n>two\nRYSWKMBDHV\n"))
        self.assertEqual(records, [qc.SequenceRecord("one", "ACGTNN"), qc.SequenceRecord("two", "RYSWKMBDHV")])

    def test_bad_inputs(self):
        examples = {
            "no records": "\n\n",
            "sequence before header": "ACGT\n>one\nACGT\n",
            "empty header": "> \nACGT\n",
            "empty sequence": ">one\n>two\nACGT\n",
            "last empty sequence": ">one\nACGT\n>two\n",
            "duplicate identifier": ">one description\nACGT\n>one different\nACGT\n",
            "unsupported RNA": ">one\nACGU\n",
            "gap": ">one\nAC-GT\n",
            "embedded space": ">one\nAC GT\n",
            "digit": ">one\nACGT2\n",
            "unsafe identifier": ">=formula\nACGT\n",
        }
        for label, text in examples.items():
            with self.subTest(label=label), self.assertRaises(qc.ValidationError):
                qc.parse_fasta(io.StringIO(text))


class ManifestTests(unittest.TestCase):
    def test_same_sample_can_have_multiple_sequences(self):
        result = qc.parse_manifest(io.StringIO("sequence_id,sample_id\na,s1\nb,s1\n"))
        self.assertEqual(result, {"a": "s1", "b": "s1"})

    def test_duplicate_id_even_when_sample_differs(self):
        with self.assertRaisesRegex(qc.ValidationError, "duplicate"):
            qc.parse_manifest(io.StringIO("sequence_id,sample_id\na,s1\na,s2\n"))

    def test_bad_columns_and_missing_values(self):
        for text in ["sample_id,sequence_id\ns1,a\n", "sequence_id,sample_id\n", "sequence_id,sample_id\na\n", "sequence_id,sample_id\na,s1,extra\n", "sequence_id,sample_id\na,\n", "sequence_id,sample_id\na,=unsafe\n"]:
            with self.subTest(text=text), self.assertRaises(qc.ValidationError):
                qc.parse_manifest(io.StringIO(text))

    def test_missing_and_extra_both_reported(self):
        records = [qc.SequenceRecord("one", "ACGT")]
        with self.assertRaisesRegex(qc.ValidationError, r"missing sequence IDs \['one'\]; extra sequence IDs \['two'\]"):
            qc.reconcile(records, {"two": "sample"})

    def test_malformed_quoted_csv_is_rejected(self):
        with self.assertRaises(csv.Error):
            qc.parse_manifest(io.StringIO('sequence_id,sample_id\na,"unterminated\n'))


class MetricTests(unittest.TestCase):
    def test_n50_is_weighted_not_median(self):
        self.assertEqual(qc.length_n50([100, 10, 10, 10, 10, 10]), 100)

    def test_n50_exact_half_and_odd_total(self):
        self.assertEqual(qc.length_n50([5, 3, 2]), 5)
        self.assertEqual(qc.length_n50([4, 3, 2]), 3)
        self.assertEqual(qc.length_n50([5]), 5)

    def test_n50_invalid(self):
        for lengths in [[], [0], [-2], [1.5], [True]]:
            with self.subTest(lengths=lengths), self.assertRaises(qc.ValidationError):
                qc.length_n50(lengths)

    def test_gc_excludes_ambiguities_and_pools_bases(self):
        result = qc.summarize([qc.SequenceRecord("a", "GCNN"), qc.SequenceRecord("b", "AAAAAA")], {"a": "s", "b": "s"})
        self.assertEqual(result["gc_fraction"], 0.25)
        self.assertEqual(result["ambiguous_bases"], 2)
        self.assertEqual(result["ambiguous_fraction"], 0.2)
        self.assertEqual(result["sequences"][0]["gc_fraction"], 1.0)
        self.assertEqual(result["sample_count"], 1)

    def test_all_ambiguous_has_null_gc(self):
        result = qc.summarize([qc.SequenceRecord("a", "NRYSWKMBDHV")], {"a": "s"})
        self.assertIsNone(result["gc_fraction"])
        self.assertIsNone(result["sequences"][0]["gc_fraction"])
        self.assertEqual(result["ambiguous_bases"], 11)
        self.assertEqual(result["sequences"][0]["n_bases"], 1)
        self.assertEqual(result["ambiguous_fraction"], 1.0)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fasta = self.root / "demo.fasta"
        self.manifest = self.root / "manifest.csv"
        self.fasta.write_text(">a\nACGTNN\n>b\nNN\n", encoding="utf-8")
        self.manifest.write_text("sequence_id,sample_id\na,s1\nb,s2\n", encoding="utf-8")

    def test_end_to_end_outputs_and_reproducibility(self):
        output = self.root / "results"
        args = ["--fasta", str(self.fasta), "--manifest", str(self.manifest), "--output-dir", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(qc.main(args), 0)
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(qc.main(args), 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
        report = json.loads((output / "report.json").read_text())
        self.assertEqual(report["metrics"]["total_bases"], 8)
        self.assertEqual(report["inputs"]["fasta"], qc.file_provenance(self.fasta))
        self.assertIsNone(report["metrics"]["sequences"][1]["gc_fraction"])
        with (output / "sequences.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[1]["gc_fraction"], "")
        self.assertIn("not evidence of organism identity", (output / "report.md").read_text())

    def test_validation_failure_does_not_create_output_directory(self):
        self.fasta.write_text(">a\nACGU\n", encoding="utf-8")
        output = self.root / "results"
        with contextlib.redirect_stderr(io.StringIO()) as error:
            result = qc.main(["--fasta", str(self.fasta), "--manifest", str(self.manifest), "--output-dir", str(output)])
        self.assertEqual(result, 2)
        self.assertFalse(output.exists())
        self.assertIn("invalid DNA", error.getvalue())

    def test_missing_file_has_clear_failure(self):
        with contextlib.redirect_stderr(io.StringIO()):
            result = qc.main(["--fasta", str(self.root / "missing"), "--manifest", str(self.manifest), "--output-dir", str(self.root / "reports")])
        self.assertEqual(result, 2)

    def test_prevent_input_overwrite(self):
        report = qc.build_report(self.fasta, self.manifest, "test")
        with self.assertRaisesRegex(qc.ValidationError, "overwrite"):
            qc.write_report(report, self.root, [self.root / "report.json"])
        self.assertFalse((self.root / "report.json").exists())

    def test_fingerprint_uses_parsed_snapshot(self):
        original = self.fasta.read_bytes()
        report = qc.build_report(self.fasta, self.manifest, "test")
        self.fasta.write_text(">changed\nAAAA\n", encoding="utf-8")
        self.assertEqual(report["inputs"]["fasta"], qc.file_provenance(self.fasta, original))
        self.assertNotEqual(report["inputs"]["fasta"], qc.file_provenance(self.fasta))


if __name__ == "__main__":
    unittest.main()
