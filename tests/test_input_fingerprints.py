import gzip
from pathlib import Path
import tempfile
import unittest
import input_fingerprints as fingerprints
from sequence_qc import ValidationError


class InputFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'reads.fastq.gz'
        self.source.write_bytes(gzip.compress(b'@read1\nACGT\n+\nIIII\n', mtime=0))
        self.manifest = self.root/'samples.csv'
        self.manifest.write_text('sample_id,fastq_path,quality_encoding\nS1,reads.fastq.gz,phred33\n')
        self.lock = self.root/'lock.json'

    def test_round_trip_preserves_input_and_pins_compressed_bytes(self):
        original = self.source.read_bytes()
        result = fingerprints.create(self.manifest, self.lock)
        self.assertEqual(result, fingerprints.verify(self.manifest, self.lock))
        self.assertEqual(result['files'][0]['bytes'], len(original))
        self.assertEqual(self.source.read_bytes(), original)

    def test_changed_compression_bytes_are_detected(self):
        fingerprints.create(self.manifest, self.lock)
        self.source.write_bytes(gzip.compress(b'@read1\nACGT\n+\nIIII\n', mtime=1))
        with self.assertRaisesRegex(ValidationError, 'mismatch'):
            fingerprints.verify(self.manifest, self.lock)

    def test_changed_sample_sheet_or_truncated_file_is_detected(self):
        fingerprints.create(self.manifest, self.lock)
        self.manifest.write_text(self.manifest.read_text().replace('S1,', 'S2,'))
        with self.assertRaises(ValidationError):
            fingerprints.verify(self.manifest, self.lock)
        self.manifest.write_text(self.manifest.read_text().replace('S2,', 'S1,'))
        self.source.write_bytes(self.source.read_bytes()[:-4])
        with self.assertRaises(ValidationError):
            fingerprints.verify(self.manifest, self.lock)

    def test_missing_input_rejected(self):
        fingerprints.create(self.manifest, self.lock)
        self.source.unlink()
        with self.assertRaises(ValidationError):
            fingerprints.verify(self.manifest, self.lock)

    def test_existing_lock_and_source_overwrites_are_refused(self):
        fingerprints.create(self.manifest, self.lock)
        with self.assertRaises(FileExistsError):
            fingerprints.create(self.manifest, self.lock)
        original = self.source.read_bytes()
        with self.assertRaises(ValidationError):
            fingerprints.create(self.manifest, self.source)
        self.assertEqual(original, self.source.read_bytes())

    def test_fingerprint_is_not_a_fastq_quality_assertion(self):
        self.source.write_bytes(b'not a fastq record')
        record = fingerprints.create(self.manifest, self.lock)
        self.assertIn('no FASTQ parsing', record['scope'])
        self.assertEqual(record, fingerprints.verify(self.manifest, self.lock))


if __name__ == '__main__':
    unittest.main()
