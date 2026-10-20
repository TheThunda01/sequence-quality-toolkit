from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fastq_qc
import input_fingerprints
from sequence_qc import ValidationError


class LockedQcTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.reads=self.root/'sample.fastq'
        self.reads.write_text('@one\nACGT\n+\nIIII\n')
        self.sheet=self.root/'samples.csv';self.sheet.write_text('sample_id,fastq_path,quality_encoding\nS1,sample.fastq,phred33\n')
        self.lock=self.root/'lock.json';input_fingerprints.create(self.sheet,self.lock)
        self.out=self.root/'out'

    def test_matching_lock_records_provenance_and_preserves_metrics(self):
        plain=fastq_qc.run(self.sheet,self.root/'plain','synthetic')
        locked=fastq_qc.run(self.sheet,self.out,'synthetic',self.lock)
        self.assertNotIn('input_lock',plain)
        self.assertEqual(plain['samples'],locked['samples'])
        self.assertEqual(locked['input_lock']['status'],'preflight_and_consumed_bytes_match')
        self.assertEqual(json.loads((self.out/'report.json').read_text()),locked)

    def test_preflight_mismatch_preserves_existing_reports(self):
        fastq_qc.run(self.sheet,self.out,'synthetic')
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        self.reads.write_text(self.reads.read_text().replace('ACGT','TGCA'))
        with self.assertRaisesRegex(ValidationError,'fingerprint'):
            fastq_qc.run(self.sheet,self.out,'synthetic',self.lock)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})

    def test_change_after_preflight_is_checked_against_consumed_bytes(self):
        process=fastq_qc.process_sample
        def change_then_read(sample, handle):
            self.reads.write_text(self.reads.read_text().replace('ACGT','TGCA'))
            return process(sample,handle)
        with patch('fastq_qc.process_sample',side_effect=change_then_read):
            with self.assertRaisesRegex(ValidationError,'consumed'):
                fastq_qc.run(self.sheet,self.out,'synthetic',self.lock)
        self.assertFalse(self.out.exists())

    def test_changed_lock_during_processing_is_rejected(self):
        process=fastq_qc.process_sample
        def read_then_change(sample,handle):
            result=process(sample,handle);self.lock.write_text('{}');return result
        with patch('fastq_qc.process_sample',side_effect=read_then_change):
            with self.assertRaisesRegex(ValidationError,'changed during'):
                fastq_qc.run(self.sheet,self.out,'synthetic',self.lock)
        self.assertFalse(self.out.exists())

    def test_lock_cannot_be_replaced_by_qc_output(self):
        self.out.mkdir();target=self.out/'report.json';target.write_bytes(self.lock.read_bytes())
        before=target.read_bytes()
        with self.assertRaisesRegex(ValidationError,'overwrite'):
            fastq_qc.run(self.sheet,self.out,'synthetic',target)
        self.assertEqual(target.read_bytes(),before)

    def test_cli_bad_lock_returns_two_without_publishing(self):
        self.lock.write_text('not JSON')
        with redirect_stderr(io.StringIO()) as errors:
            code=fastq_qc.main(['--manifest',str(self.sheet),'--output-dir',str(self.out),'--input-lock',str(self.lock)])
        self.assertEqual(code,2);self.assertIn('Input/output error',errors.getvalue())
        self.assertFalse(self.out.exists())


if __name__ == '__main__':
    unittest.main()
