"""Create and verify a byte-fingerprint lock for a declared FASTQ sample sheet.

This is a separate preflight: files are not parsed, rewritten, or biologically validated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from fastq_qc import parse_sample_manifest
from sequence_qc import ValidationError


def fingerprint(path):
    digest, size = hashlib.sha256(), 0
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block); size += len(block)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def snapshot(manifest):
    samples, source = parse_sample_manifest(Path(manifest))
    records = []
    for sample in samples:
        records.append({'sample_id': sample.sample_id, 'fastq_path': sample.manifest_path,
                        'quality_encoding': sample.quality_encoding, **fingerprint(sample.path)})
    return {'schema_version':'1.0', 'mode':'fastq_input_byte_fingerprints',
            'scope':'Exact sample-sheet and raw file bytes only; no FASTQ parsing or quality/identity judgement',
            'manifest_sha256':source['sha256'], 'files':records}


def create(manifest, lock):
    manifest, lock = Path(manifest), Path(lock)
    samples, _ = parse_sample_manifest(manifest)
    if lock.resolve() in {manifest.resolve(), *(sample.path.resolve() for sample in samples)}:
        raise ValidationError('Fingerprint lock cannot overwrite the sample sheet or an input')
    result = snapshot(manifest)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    return result


def verify(manifest, lock):
    expected = json.loads(Path(lock).read_text())
    actual = snapshot(manifest)
    if expected != actual:
        raise ValidationError('Input fingerprint mismatch: sample sheet or raw file bytes changed')
    return actual


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['create','verify'])
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--lock', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (create if args.mode=='create' else verify)(args.manifest, args.lock)
    except (ValidationError, ValueError, OSError, UnicodeError) as error:
        print(f'Input fingerprint check failed: {error}', file=sys.stderr); return 2
    print(f"{args.mode}: {len(result['files'])} declared input file(s) fingerprinted; FASTQ semantics not assessed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
