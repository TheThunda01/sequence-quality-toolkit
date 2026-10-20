import contextlib
import csv
import gzip
import hashlib
import io
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest

import fastq_qc as fq
from sequence_qc import ValidationError


class FastqParserTests(unittest.TestCase):
    def test_wrapped_records_and_quality_delimiter_characters(self):
        text = "@r1 description\nac\ngt\n+r1\n@+\nI!\n@r2\nNN\n+\n~~\n"
        result = list(fq.iter_fastq(io.StringIO(text)))
        self.assertEqual(result, [fq.FastqRecord("r1", "ACGT", "@+I!"), fq.FastqRecord("r2", "NN", "~~")])

    def test_crlf_and_missing_final_newline(self):
        text = "@r1\r\nACGT\r\n+\r\n!!!!"
        self.assertEqual(list(fq.iter_fastq(io.StringIO(text)))[0].quality, "!!!!")

    def test_quality_encoding_bounds(self):
        record = list(fq.iter_fastq(io.StringIO("@r\nAC\n+\n!~\n")))[0]
        metrics = fq.read_metrics(record)
        self.assertEqual(metrics["min_phred"], 0)
        self.assertEqual(metrics["mean_phred"], 46.5)

    def test_malformed_input(self):
        cases = {
            "empty": "", "blank": "\n", "header": "r\nAC\n+\n!!\n",
            "empty header": "@\nAC\n+\n!!\n", "missing separator": "@r\nAC\n",
            "empty seq": "@r\n+\n!!\n", "wrong plus ID": "@r\nAC\n+other\n!!\n",
            "short quality": "@r\nAC\n+\n!\n", "long quality": "@r\nAC\n+\n!!!\n",
            "quality space": "@r\nAC\n+\n! \n", "quality below33": "@r\nAC\n+\n!\x00\n",
            "quality above126": "@r\nAC\n+\n!\x7f\n", "RNA": "@r\nAU\n+\n!!\n",
            "embedded whitespace": "@r\nA C\n+\n!!!\n", "trailing garbage": "@r\nAC\n+\n!!\nGARBAGE\n",
            "unicode case expansion": "@r\nß\n+\n!\n",
        }
        for name, text in cases.items():
            with self.subTest(name=name), self.assertRaises(ValidationError):
                list(fq.iter_fastq(io.StringIO(text)))

    def test_read_length_limit(self):
        with self.assertRaisesRegex(ValidationError, "exceeds"):
            list(fq.iter_fastq(io.StringIO("@r\nACG\n+\n!!!\n"), max_read_length=2))

    def test_parser_does_not_read_entire_stream(self):
        class ReadlineOnly(io.StringIO):
            def read(self, *_args):
                raise AssertionError("Parser tried to read the full stream")
        stream = ReadlineOnly("@a\nAC\n+\n!!\n@b\nGT\n+\nII\n")
        reader = fq.iter_fastq(stream)
        self.assertEqual(next(reader).read_id, "a")
        self.assertLess(stream.tell(), len(stream.getvalue()))
        self.assertEqual(next(reader).read_id, "b")

    def test_q_error_arithmetic_and_ambiguous_gc(self):
        metrics = fq.read_metrics(fq.FastqRecord("a", "GCNN", "!5?I"))
        self.assertEqual(metrics["q20_fraction"], 0.75)
        self.assertEqual(metrics["q30_fraction"], 0.5)
        self.assertAlmostEqual(metrics["expected_errors_from_qualities"], 1.0111)
        self.assertEqual(metrics["gc_fraction"], 1.0)
        self.assertIsNone(fq.read_metrics(fq.FastqRecord("b", "NN", "II"))["gc_fraction"])


class FastqFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b"@a\nACGT\n+\nIIII\n@b\nNN\n+\n!!\n"
        self.input = self.root / "input.fastq"
        self.input.write_bytes(self.data)
        self.manifest = self.root / "samples.csv"
        self.manifest.write_text("sample_id,fastq_path,quality_encoding\ns1,input.fastq,phred33\n", encoding="utf-8")

    def test_plain_gzip_same_metrics_and_exact_raw_hashes(self):
        gz = self.root / "input.gz"
        gz.write_bytes(gzip.compress(self.data, mtime=0))
        summaries = []
        for path in [self.input, gz]:
            sample = fq.SampleInput("s1", path, path.name, "phred33")
            summary, cycles, lengths = fq.process_sample(sample, io.StringIO())
            self.assertEqual(summary["input_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(summary["input_bytes"], len(path.read_bytes()))
            summaries.append(summary)
        excluded = {"input_sha256", "input_bytes", "input_name", "compression"}
        self.assertEqual({k:v for k,v in summaries[0].items() if k not in excluded}, {k:v for k,v in summaries[1].items() if k not in excluded})

    def test_base_weighted_summary_and_cycle_denominators(self):
        summary, cycles, lengths = fq.process_sample(fq.SampleInput("s1", self.input, "input.fastq", "phred33"), io.StringIO())
        self.assertEqual(summary["read_count"], 2)
        self.assertEqual(summary["total_bases"], 6)
        self.assertEqual(summary["base_weighted_mean_phred"], round(160/6, 6))
        self.assertEqual(summary["q30_fraction"], round(4/6, 6))
        self.assertEqual(cycles[0]["observed_bases"], 2)
        self.assertEqual(cycles[2]["observed_bases"], 1)
        self.assertEqual(cycles[0]["n_fraction"], 0.5)
        self.assertEqual(lengths, [{"sample_id":"s1","length":2,"read_count":1},{"sample_id":"s1","length":4,"read_count":1}])

    def test_multimember_gzip(self):
        path = self.root / "multi.gz"
        path.write_bytes(gzip.compress(b"@a\nAC\n+\nII\n", mtime=0) + gzip.compress(b"@b\nGT\n+\nII\n", mtime=0))
        summary, _, _ = fq.process_sample(fq.SampleInput("s1", path, path.name, "phred33"), io.StringIO())
        self.assertEqual(summary["read_count"], 2)
        self.assertEqual(summary["input_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_manifest_validation(self):
        cases = [
            "sample_id,fastq_path,quality_encoding\ns1,input.fastq,phred64\n",
            "sample_id,fastq_path,quality_encoding\ns1,input.fastq,phred33\ns1,input2.fastq,phred33\n",
            "sample_id,fastq_path,quality_encoding\ns1,input.fastq,phred33\ns2,./input.fastq,phred33\n",
            "sample_id,fastq_path,quality_encoding\ns1,missing.fastq,phred33\n",
            "sample_id,fastq_path,quality_encoding\ns1,input.fastq\n",
            "sample_id,fastq_path,quality_encoding\n",
            "sample_id,path,quality_encoding\ns1,input.fastq,phred33\n",
        ]
        for content in cases:
            self.manifest.write_text(content)
            with self.subTest(content=content), self.assertRaises(ValidationError):
                fq.parse_sample_manifest(self.manifest)

    def test_success_is_deterministic_and_preserves_input(self):
        output = self.root / "results"
        report = fq.run(self.manifest, output, "synthetic")
        before = {path.name:path.read_bytes() for path in output.iterdir()}
        fq.run(self.manifest, output, "synthetic")
        self.assertEqual(before, {path.name:path.read_bytes() for path in output.iterdir()})
        self.assertEqual(self.input.read_bytes(), self.data)
        self.assertEqual(len(list(output.iterdir())), len(fq.OUTPUT_NAMES))
        rows = [json.loads(line) for line in (output / "read_metrics.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[1]["gc_fraction"])
        self.assertEqual(report["manifest"]["sha256"], hashlib.sha256(self.manifest.read_bytes()).hexdigest())

    def test_bad_later_sample_keeps_previous_reports_unchanged(self):
        output = self.root / "results"
        fq.run(self.manifest, output, "original")
        before = {path.name:path.read_bytes() for path in output.iterdir()}
        bad = self.root / "bad.fastq"
        bad.write_text("@bad\nAC\n+\nI\n")
        self.manifest.write_text("sample_id,fastq_path,quality_encoding\ns1,input.fastq,phred33\ns2,bad.fastq,phred33\n")
        with self.assertRaises(ValidationError):
            fq.run(self.manifest, output, "broken")
        self.assertEqual(before, {path.name:path.read_bytes() for path in output.iterdir()})

    def test_corrupt_gzip_reports_failure_without_new_results(self):
        path = self.root / "bad.gz"
        path.write_bytes(gzip.compress(self.data)[:-5])
        self.manifest.write_text("sample_id,fastq_path,quality_encoding\ns1,bad.gz,phred33\n")
        output = self.root / "results"
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fq.main(["--manifest",str(self.manifest),"--output-dir",str(output)]), 2)
        self.assertFalse(output.exists())

    def test_output_cannot_overwrite_input(self):
        collision = self.root / "report.json"
        collision.write_bytes(self.data)
        self.manifest.write_text("sample_id,fastq_path,quality_encoding\ns1,report.json,phred33\n")
        with self.assertRaisesRegex(ValidationError, "overwrite"):
            fq.run(self.manifest, self.root, "test")
        self.assertEqual(collision.read_bytes(), self.data)


class PublicExampleTests(unittest.TestCase):
    def test_public_fixture_provenance_and_record_count(self):
        root = Path(__file__).resolve().parents[1]
        metadata = json.loads((root / "examples/public/provenance.json").read_text())
        path = root / "examples/public" / metadata["subset_filename"]
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["subset_compressed_sha256"])
        self.assertEqual(hashlib.sha256(gzip.decompress(raw)).hexdigest(), metadata["subset_uncompressed_sha256"])
        with gzip.open(path, "rt", encoding="ascii") as handle:
            records = list(fq.iter_fastq(handle))
        self.assertEqual(len(records), 1000)
        self.assertEqual(records[0].read_id, metadata["first_read_id"])
        self.assertEqual(records[-1].read_id, metadata["last_read_id"])

    def test_retrieval_script_rejects_changed_source(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("fetch_public_example", root / "scripts/fetch_public_example.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "changed.fastq.gz"
            source.write_bytes(b"not the verified archive")
            output = Path(temp) / "result"
            with self.assertRaisesRegex(ValueError, "does not match"):
                module.subset(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
