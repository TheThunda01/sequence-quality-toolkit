import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from fastq_qc import FastqRecord
import paired_fastq_check as pairs
from sequence_qc import ValidationError


def fastq(name, sequence="ACGT", quality=None):
    return f"@{name}\n{sequence}\n+\n{quality or 'I' * len(sequence)}\n"


class PairNameTests(unittest.TestCase):
    def test_suffix_strips_only_supported_terminal_mate(self):
        record = FastqRecord("cluster#0/2", "AC", "II", "cluster#0/2 description")
        self.assertEqual(pairs.normalize_name(record, "suffix"), pairs.PairName("cluster#0", 2))

    def test_illumina_retains_cluster_key(self):
        header = "MACHINE:1:FLOW:2:1101:-23:450 2:N:0:ACGT+TGCA"
        record = FastqRecord(header.split()[0], "AC", "II", header)
        self.assertEqual(pairs.normalize_name(record, "illumina"), pairs.PairName("MACHINE:1:FLOW:2:1101:-23:450", 2))

    def test_reject_unrecognized_or_ambiguous_names(self):
        cases = [
            ("plain_id", "suffix"), ("name/3", "suffix"), ("nested/1/2", "suffix"),
            ("name/1 1:N:0:ACGT", "suffix"), ("name/1 description /2", "suffix"),
            ("plain_id 1:N:0:ACGT", "illumina"),
            ("M:1:F:1:1:2:3", "illumina"),
            ("M:1:F:1:1:2:3 1:N:0:ACGT unexpected", "illumina"),
            ("M:1:F:1:1:2:3 1:n:0:ACGT", "illumina"),
            ("M:1:F:1:1:2:3 1:N:0:", "illumina"),
            ("name/1", "guess"),
        ]
        for header, convention in cases:
            with self.subTest(header=header, convention=convention), self.assertRaises(ValidationError):
                pairs.normalize_name(FastqRecord(header.split()[0], "A", "I", header), convention)


class PairStreamTests(unittest.TestCase):
    def test_valid_pairs_need_not_be_same_length_or_complements(self):
        result = pairs.validate_streams(io.StringIO(fastq("x/1", "AAAA")), io.StringIO(fastq("x/2", "GGGGGG")), "suffix")
        self.assertEqual(result, {"validated_pairs":1,"r1_read_count":1,"r2_read_count":1})

    def test_read_order_is_checked_not_repaired(self):
        r1 = fastq("a/1") + fastq("b/1")
        r2 = fastq("b/2") + fastq("a/2")
        with self.assertRaisesRegex(ValidationError, "Pair 1: normalized identifiers differ"):
            pairs.validate_streams(io.StringIO(r1), io.StringIO(r2), "suffix")

    def test_mate_direction_required(self):
        for a, b in [("a/2","a/1"),("a/1","a/1"),("a/2","a/2")]:
            with self.subTest(a=a,b=b), self.assertRaisesRegex(ValidationError, "expected mate 1"):
                pairs.validate_streams(io.StringIO(fastq(a)), io.StringIO(fastq(b)), "suffix")

    def test_count_mismatch_in_either_file(self):
        r1 = fastq("a/1") + fastq("b/1")
        r2 = fastq("a/2")
        with self.assertRaisesRegex(ValidationError, "R2 ended first"):
            pairs.validate_streams(io.StringIO(r1), io.StringIO(r2), "suffix")
        with self.assertRaisesRegex(ValidationError, "R1 ended first"):
            pairs.validate_streams(io.StringIO(fastq("a/1")), io.StringIO(r2 + fastq("b/2")), "suffix")

    def test_empty_inputs_never_pass(self):
        for r1, r2 in [("",""),("",fastq("a/2")),(fastq("a/1"),"")]:
            with self.subTest(r1=r1,r2=r2), self.assertRaisesRegex(ValidationError, "empty"):
                pairs.validate_streams(io.StringIO(r1), io.StringIO(r2), "suffix")

    def test_illumina_pair_uses_cluster_and_mate_not_filter_flag(self):
        r1 = fastq("M:1:F:1:1:2:3 1:N:0:ACGT")
        r2 = fastq("M:1:F:1:1:2:3 2:Y:0:ACGT")
        self.assertEqual(pairs.validate_streams(io.StringIO(r1), io.StringIO(r2), "illumina")["validated_pairs"], 1)

    def test_single_end_archive_names_do_not_silently_pair(self):
        with self.assertRaisesRegex(ValidationError, "Unrecognized"):
            pairs.validate_streams(io.StringIO(fastq("ERR458493.1")), io.StringIO(fastq("ERR458493.1")), "suffix")

    def test_case_sensitive_pair_keys(self):
        with self.assertRaisesRegex(ValidationError, "differ"):
            pairs.validate_streams(io.StringIO(fastq("Pair/1")), io.StringIO(fastq("pair/2")), "suffix")

    def test_malformed_fastq_fails_before_pairing(self):
        with self.assertRaisesRegex(ValidationError, "shorter"):
            pairs.validate_streams(io.StringIO(fastq("a/1")), io.StringIO("@a/2\nACGT\n+\nI\n"), "suffix")


class PairFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.r1 = self.root / "r1.fastq"
        self.r2 = self.root / "r2.fastq"
        self.r1.write_text(fastq("a/1") + fastq("b/1"))
        self.r2.write_text(fastq("a/2") + fastq("b/2"))
        self.output = self.root / "reports"

    def run_check(self, r1=None, r2=None):
        return pairs.run(r1 or self.r1, r2 or self.r2, self.output, "suffix", "phred33", "synthetic", "Synthetic pairs")

    def test_plain_gzip_pair_hashes_and_no_input_changes(self):
        raw1, raw2 = self.r1.read_bytes(), self.r2.read_bytes()
        gz = self.root / "r2.gz"
        gz.write_bytes(gzip.compress(raw2, mtime=0))
        report = self.run_check(r2=gz)
        self.assertEqual(report["metrics"]["validated_pairs"], 2)
        self.assertEqual(report["inputs"]["r1"]["sha256"], hashlib.sha256(raw1).hexdigest())
        self.assertEqual(report["inputs"]["r2"]["sha256"], hashlib.sha256(gz.read_bytes()).hexdigest())
        self.assertEqual(report["inputs"]["r2"]["bytes"], len(gz.read_bytes()))
        self.assertEqual(self.r1.read_bytes(), raw1)
        self.assertEqual(self.r2.read_bytes(), raw2)

    def test_output_deterministic_and_later_failure_preserves_it(self):
        self.run_check()
        before = {path.name:path.read_bytes() for path in self.output.iterdir()}
        self.run_check()
        self.assertEqual(before, {path.name:path.read_bytes() for path in self.output.iterdir()})
        self.r2.write_text(fastq("a/2") + fastq("wrong/2"))
        with self.assertRaises(ValidationError):
            self.run_check()
        self.assertEqual(before, {path.name:path.read_bytes() for path in self.output.iterdir()})

    def test_same_input_and_output_collisions_blocked(self):
        with self.assertRaisesRegex(ValidationError,"different input"):
            self.run_check(r2=self.r1)
        colliding = self.root / "report.json"
        colliding.write_bytes(self.r1.read_bytes())
        with self.assertRaisesRegex(ValidationError,"overwrite"):
            pairs.run(colliding, self.r2, self.root, "suffix", "phred33", "s", "test")

    def test_unsupported_encoding_blocked(self):
        with self.assertRaisesRegex(ValidationError,"phred33"):
            pairs.run(self.r1, self.r2, self.output, "suffix", "phred64", "s", "test")

    def test_corrupt_gzip_exits_cleanly_without_report(self):
        bad = self.root / "bad.gz"
        bad.write_bytes(gzip.compress(self.r2.read_bytes())[:-3])
        args = ["--read1",str(self.r1),"--read2",str(bad),"--name-convention","suffix","--quality-encoding","phred33","--output-dir",str(self.output)]
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(pairs.main(args), 2)
        self.assertIn("Pair-validation error", error.getvalue())
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
