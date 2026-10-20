"""Streaming, descriptive FASTQ quality summaries; explicit Phred+33 only."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterator, TextIO
import zlib

from sequence_qc import ALPHABET, CANONICAL, ValidationError, fraction, valid_identifier

VERSION = "0.2.0"
MAX_READ_LENGTH = 1_000_000
OUTPUT_NAMES = ("report.json", "report.md", "samples.csv", "cycles.csv", "length_distribution.csv", "read_metrics.jsonl")


@dataclass(frozen=True)
class FastqRecord:
    read_id: str
    sequence: str
    quality: str


@dataclass(frozen=True)
class SampleInput:
    sample_id: str
    path: Path
    manifest_path: str
    quality_encoding: str


def without_newline(line: str) -> str:
    return line.removesuffix("\n").removesuffix("\r")


def iter_fastq(handle: TextIO, max_read_length: int = MAX_READ_LENGTH) -> Iterator[FastqRecord]:
    """Parse wrapped FASTQ; quality @ and + characters are data, not headers."""
    if max_read_length < 1:
        raise ValidationError("max_read_length must be positive")
    number = 0
    while True:
        raw = handle.readline()
        if not raw:
            if number == 0:
                raise ValidationError("FASTQ is empty")
            return
        number += 1
        header = without_newline(raw)
        if not header.startswith("@") or not header[1:].strip():
            raise ValidationError(f"FASTQ record {number}: expected a nonempty @ header")
        read_id = header[1:].split()[0]
        if any(ord(char) < 33 or ord(char) > 126 for char in read_id):
            raise ValidationError(f"FASTQ record {number}: read ID must be printable ASCII")
        pieces = []
        sequence_length = 0
        while True:
            raw = handle.readline()
            if not raw:
                raise ValidationError(f"FASTQ record {number}: missing + separator")
            line = without_newline(raw)
            if line.startswith("+"):
                plus_id = line[1:].strip()
                if plus_id and plus_id.split()[0] != read_id:
                    raise ValidationError(f"FASTQ record {number}: + identifier differs from @ identifier")
                break
            if not line.isascii():
                raise ValidationError(f"FASTQ record {number}: non-ASCII DNA characters")
            sequence = line.upper()
            if not sequence or set(sequence) - ALPHABET:
                raise ValidationError(f"FASTQ record {number}: empty sequence line or unsupported DNA symbols")
            sequence_length += len(sequence)
            if sequence_length > max_read_length:
                raise ValidationError(f"FASTQ record {number}: read exceeds {max_read_length} symbols")
            pieces.append(sequence)
        if sequence_length == 0:
            raise ValidationError(f"FASTQ record {number}: empty sequence")
        qualities = []
        quality_length = 0
        while quality_length < sequence_length:
            raw = handle.readline()
            if not raw:
                raise ValidationError(f"FASTQ record {number}: quality string shorter than sequence")
            line = without_newline(raw)
            if not line or any(ord(char) < 33 or ord(char) > 126 for char in line):
                raise ValidationError(f"FASTQ record {number}: Phred+33 qualities must be ASCII 33..126")
            quality_length += len(line)
            if quality_length > sequence_length:
                raise ValidationError(f"FASTQ record {number}: quality string longer than sequence")
            qualities.append(line)
        yield FastqRecord(read_id, "".join(pieces), "".join(qualities))


def parse_sample_manifest(path: Path) -> tuple[list[SampleInput], dict]:
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
    if reader.fieldnames != ["sample_id", "fastq_path", "quality_encoding"]:
        raise ValidationError("FASTQ manifest header must be exactly sample_id,fastq_path,quality_encoding")
    samples, ids, paths = [], set(), set()
    for line_number, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValidationError(f"Manifest line {line_number}: expected three columns")
        sample_id = row["sample_id"]
        valid_identifier(sample_id, f"Manifest line {line_number} sample_id")
        if sample_id in ids:
            raise ValidationError(f"Manifest line {line_number}: duplicate sample_id {sample_id!r}")
        if row["quality_encoding"] != "phred33":
            raise ValidationError(f"Manifest line {line_number}: declare quality_encoding as phred33; encoding is not guessed")
        if not row["fastq_path"] or row["fastq_path"] != row["fastq_path"].strip():
            raise ValidationError(f"Manifest line {line_number}: missing or whitespace-padded fastq_path")
        source = Path(row["fastq_path"])
        resolved = (path.parent / source).resolve()
        if resolved in paths:
            raise ValidationError(f"Manifest line {line_number}: the same input file appears more than once")
        if not resolved.is_file():
            raise ValidationError(f"Manifest line {line_number}: FASTQ file does not exist: {row['fastq_path']}")
        ids.add(sample_id)
        paths.add(resolved)
        samples.append(SampleInput(sample_id, resolved, row["fastq_path"], "phred33"))
    if not samples:
        raise ValidationError("FASTQ manifest has no samples")
    return samples, {"name": path.name, "sha256": hashlib.sha256(raw).hexdigest()}


class DigestReader(io.RawIOBase):
    """Hash source bytes as they enter the buffered/decompression reader."""

    def __init__(self, raw):
        self.raw = raw
        self.digest = hashlib.sha256()
        self.byte_count = 0

    def readable(self):
        return True

    def readinto(self, target):
        data = self.raw.read(len(target))
        count = len(data)
        target[:count] = data
        self.digest.update(data)
        self.byte_count += count
        return count

    def close(self):
        try:
            self.raw.close()
        finally:
            super().close()


@contextmanager
def open_fastq(path: Path):
    """Read plain text or gzip, hashing the original bytes in the same pass."""
    raw = path.open("rb")
    hashed = DigestReader(raw)
    buffered = io.BufferedReader(hashed)
    try:
        is_gzip = buffered.peek(2)[:2] == b"\x1f\x8b"
        binary = gzip.GzipFile(fileobj=buffered, mode="rb") if is_gzip else buffered
        with io.TextIOWrapper(binary, encoding="ascii", newline="") as text:
            yield text, hashed, is_gzip
    finally:
        buffered.close()


def read_metrics(record: FastqRecord) -> dict:
    qualities = [ord(char) - 33 for char in record.quality]
    counts = Counter(record.sequence)
    canonical = sum(counts[base] for base in CANONICAL)
    length = len(record.sequence)
    return {
        "read_id": record.read_id,
        "length": length,
        "gc_fraction": fraction(counts["G"] + counts["C"], canonical),
        "canonical_bases": canonical,
        "ambiguous_bases": length - canonical,
        "n_bases": counts["N"],
        "mean_phred": round(sum(qualities) / length, 6),
        "min_phred": min(qualities),
        "q20_fraction": fraction(sum(q >= 20 for q in qualities), length),
        "q30_fraction": fraction(sum(q >= 30 for q in qualities), length),
        "expected_errors_from_qualities": round(math.fsum(10 ** (-q / 10) for q in qualities), 8),
    }


def process_sample(sample: SampleInput, reads_handle: TextIO) -> tuple[dict, list[dict], list[dict]]:
    lengths, symbols, quality_hist = Counter(), Counter(), Counter()
    # Only fixed-size counters per observed cycle are retained, not reads.
    cycles: list[dict] = []
    count = 0
    with open_fastq(sample.path) as (handle, digest, compressed):
        for count, record in enumerate(iter_fastq(handle), 1):
            metrics = read_metrics(record)
            reads_handle.write(json.dumps({"sample_id": sample.sample_id, "read_index": count, **metrics}, sort_keys=True, allow_nan=False) + "\n")
            lengths[len(record.sequence)] += 1
            symbols.update(record.sequence)
            qualities = [ord(char) - 33 for char in record.quality]
            quality_hist.update(qualities)
            for index, (base, quality) in enumerate(zip(record.sequence, qualities)):
                if index == len(cycles):
                    cycles.append({"n": 0, "sum_phred": 0, "n_bases": 0, "ambiguous_bases": 0, "q20": 0, "q30": 0})
                cycle = cycles[index]
                cycle["n"] += 1
                cycle["sum_phred"] += quality
                cycle["n_bases"] += base == "N"
                cycle["ambiguous_bases"] += base not in CANONICAL
                cycle["q20"] += quality >= 20
                cycle["q30"] += quality >= 30
        source_hash = digest.digest.hexdigest()
        source_bytes = digest.byte_count
    total = sum(length * number for length, number in lengths.items())
    canonical = sum(symbols[base] for base in CANONICAL)
    quality_sum = sum(q * n for q, n in quality_hist.items())
    expected_errors = math.fsum(number * 10 ** (-q / 10) for q, number in sorted(quality_hist.items()))
    summary = {
        "sample_id": sample.sample_id,
        "input_name": sample.path.name,
        "input_sha256": source_hash,
        "input_bytes": source_bytes,
        "compression": "gzip" if compressed else "none",
        "quality_encoding": "phred33",
        "read_count": count,
        "total_bases": total,
        "min_length": min(lengths),
        "max_length": max(lengths),
        "mean_length": round(total / count, 6),
        "canonical_bases": canonical,
        "ambiguous_bases": total - canonical,
        "n_bases": symbols["N"],
        "gc_fraction": fraction(symbols["G"] + symbols["C"], canonical),
        "ambiguous_fraction": fraction(total - canonical, total),
        "n_fraction": fraction(symbols["N"], total),
        "base_weighted_mean_phred": round(quality_sum / total, 6),
        "q20_fraction": fraction(sum(n for q, n in quality_hist.items() if q >= 20), total),
        "q30_fraction": fraction(sum(n for q, n in quality_hist.items() if q >= 30), total),
        "mean_expected_errors_per_read": round(expected_errors / count, 8),
        "quality_histogram": {str(q): n for q, n in sorted(quality_hist.items())},
        "symbol_counts": {base: symbols[base] for base in sorted(ALPHABET)},
    }
    cycle_rows = [{
        "sample_id": sample.sample_id, "cycle": i + 1, "observed_bases": cycle["n"],
        "mean_phred": round(cycle["sum_phred"] / cycle["n"], 6),
        "q20_fraction": fraction(cycle["q20"], cycle["n"]),
        "q30_fraction": fraction(cycle["q30"], cycle["n"]),
        "n_fraction": fraction(cycle["n_bases"], cycle["n"]),
        "ambiguous_fraction": fraction(cycle["ambiguous_bases"], cycle["n"]),
    } for i, cycle in enumerate(cycles)]
    length_rows = [{"sample_id": sample.sample_id, "length": length, "read_count": n} for length, n in sorted(lengths.items())]
    return summary, cycle_rows, length_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(report: dict) -> str:
    lines = ["# FASTQ quality summary", "", f"Dataset label supplied by the caller: {report['dataset_label']}", "",
             "All samples were explicitly declared Phred+33. No reads were changed or filtered.", "",
             "| Sample | Reads | Bases | Mean Phred (base weighted) | Q30 fraction | N fraction |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for sample in report["samples"]:
        lines.append(f"| {sample['sample_id']} | {sample['read_count']} | {sample['total_bases']} | {sample['base_weighted_mean_phred']:.3f} | {sample['q30_fraction']:.4f} | {sample['n_fraction']:.4f} |")
    lines.extend(["", "Q20 and Q30 are descriptive score thresholds, not validated acceptance rules. Quality scores are base-caller estimates; they do not measure alignment quality, contamination, organism identity, or biological function.", "",
                  "Cycle summaries use only reads reaching that cycle. These outputs describe the provided files, not an entire experiment unless those files are complete and appropriately selected.", "",
                  "Read-level results are in `read_metrics.jsonl`; sample-level values in `samples.csv`; per-cycle summaries in `cycles.csv`; exact length counts in `length_distribution.csv`. Input fingerprints and quality histograms are in `report.json`.", ""])
    return "\n".join(lines)


def run(manifest_path: Path, output_dir: Path, dataset_label: str) -> dict:
    samples, manifest_provenance = parse_sample_manifest(manifest_path)
    inputs = {manifest_path.resolve(), *(sample.path.resolve() for sample in samples)}
    if any((output_dir / name).resolve() in inputs for name in OUTPUT_NAMES):
        raise ValidationError("An output path would overwrite an input file")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".fastq_qc_", dir=output_dir.parent) as temp:
        staging = Path(temp)
        summaries, cycles, lengths = [], [], []
        with (staging / "read_metrics.jsonl").open("w", encoding="utf-8") as reads_handle:
            for sample in samples:
                summary, cycle_rows, length_rows = process_sample(sample, reads_handle)
                summaries.append(summary)
                cycles.extend(cycle_rows)
                lengths.extend(length_rows)
        report = {
            "schema_version": "2.0", "tool_version": VERSION, "mode": "fastq",
            "dataset_label": dataset_label, "manifest": manifest_provenance,
            "scope": "Descriptive read-quality summaries only; no trimming, alignment, classification, or biological inference.",
            "max_read_length": MAX_READ_LENGTH,
            "samples": summaries,
        }
        (staging / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        (staging / "report.md").write_text(report_markdown(report), encoding="utf-8")
        scalar_summaries = [{k: v for k, v in row.items() if not isinstance(v, dict)} for row in summaries]
        write_csv(staging / "samples.csv", scalar_summaries)
        write_csv(staging / "cycles.csv", cycles)
        write_csv(staging / "length_distribution.csv", lengths)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            os.replace(staging / name, output_dir / name)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-label", default="Unspecified inputs; source not independently verified")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    try:
        report = run(args.manifest, args.output_dir, args.dataset_label)
    except (ValidationError, OSError, UnicodeError, csv.Error, EOFError, zlib.error) as error:
        print(f"Input/output error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output_dir / 'report.json'} ({len(report['samples'])} samples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
