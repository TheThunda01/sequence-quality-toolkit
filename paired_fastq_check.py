"""Validate positional read-pair naming/counts, without rewriting FASTQ files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from itertools import zip_longest
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zlib

from fastq_qc import FastqRecord, VERSION, iter_fastq, open_fastq
from sequence_qc import ValidationError, valid_identifier

SUFFIX_NAME = re.compile(r"(?P<id>[A-Za-z0-9][A-Za-z0-9_.:#-]*)/(?P<mate>[12])\Z")
ILLUMINA_ID = re.compile(r"[A-Za-z0-9_.-]+:[0-9]+:[A-Za-z0-9_.-]+:[0-9]+:[0-9]+:-?[0-9]+:-?[0-9]+\Z")
ILLUMINA_MATE = re.compile(r"(?P<mate>[12]):[YN]:[0-9]+:[A-Za-z0-9+.-]+\Z")


@dataclass(frozen=True)
class PairName:
    pair_id: str
    mate: int


def normalize_name(record: FastqRecord, convention: str) -> PairName:
    """Recognize only the explicitly selected, documented name grammar."""
    tokens = (record.header or record.read_id).split()
    if not tokens:
        raise ValidationError("Empty read header cannot identify a pair")
    if convention == "suffix":
        match = SUFFIX_NAME.fullmatch(tokens[0])
        if not match:
            raise ValidationError(f"Unrecognized /1 or /2 suffix name: {tokens[0]!r}")
        # Do not silently choose between two simultaneously present mate labels.
        if any(ILLUMINA_MATE.fullmatch(token) or token in {"/1", "/2"} for token in tokens[1:]):
            raise ValidationError("Ambiguous header combines suffix and Illumina mate conventions")
        return PairName(match["id"], int(match["mate"]))
    if convention == "illumina":
        if len(tokens) != 2 or not ILLUMINA_ID.fullmatch(tokens[0]):
            raise ValidationError("Unrecognized Illumina header: expected a seven-field cluster ID and one mate token")
        match = ILLUMINA_MATE.fullmatch(tokens[1])
        if not match:
            raise ValidationError("Unrecognized Illumina mate token: expected 1:N:0:index or 2:N:0:index (Y also allowed)")
        return PairName(tokens[0], int(match["mate"]))
    raise ValidationError("Choose name convention suffix or illumina explicitly")


def validate_streams(read1, read2, convention: str) -> dict:
    """Read streams together; fail on the first positional mismatch."""
    sentinel = object()
    count = 0
    for ordinal, (record1, record2) in enumerate(zip_longest(iter_fastq(read1), iter_fastq(read2), fillvalue=sentinel), 1):
        if record1 is sentinel or record2 is sentinel:
            ended = "R1" if record1 is sentinel else "R2"
            raise ValidationError(f"Different read counts at pair {ordinal}: {ended} ended first")
        try:
            name1 = normalize_name(record1, convention)
            name2 = normalize_name(record2, convention)
        except ValidationError as error:
            raise ValidationError(f"Pair {ordinal}: {error}") from error
        if name1.mate != 1 or name2.mate != 2:
            raise ValidationError(f"Pair {ordinal}: expected mate 1 in R1 and mate 2 in R2, found {name1.mate} and {name2.mate}")
        if name1.pair_id != name2.pair_id:
            raise ValidationError(f"Pair {ordinal}: normalized identifiers differ ({name1.pair_id!r} vs {name2.pair_id!r})")
        count += 1
    return {"validated_pairs": count, "r1_read_count": count, "r2_read_count": count}


def run(read1_path: Path, read2_path: Path, output_dir: Path, convention: str, quality_encoding: str, sample_id: str, dataset_label: str) -> dict:
    valid_identifier(sample_id, "sample_id")
    if convention not in {"suffix", "illumina"}:
        raise ValidationError("Choose name convention suffix or illumina explicitly")
    if quality_encoding != "phred33":
        raise ValidationError("Only declared phred33 input is supported; encoding is not inferred")
    paths = [read1_path.resolve(), read2_path.resolve()]
    if paths[0] == paths[1]:
        raise ValidationError("R1 and R2 must be different input files")
    names = ("report.json", "report.md")
    if any((output_dir / name).resolve() in paths for name in names):
        raise ValidationError("An output path would overwrite an input file")
    with open_fastq(paths[0]) as (read1, hash1, gzip1), open_fastq(paths[1]) as (read2, hash2, gzip2):
        metrics = validate_streams(read1, read2, convention)
        inputs = {
            "r1": {"name": paths[0].name, "sha256": hash1.digest.hexdigest(), "bytes": hash1.byte_count, "compression": "gzip" if gzip1 else "none"},
            "r2": {"name": paths[1].name, "sha256": hash2.digest.hexdigest(), "bytes": hash2.byte_count, "compression": "gzip" if gzip2 else "none"},
        }
    report = {
        "schema_version": "1.0", "tool_version": VERSION,
        "mode": "paired_fastq_consistency", "sample_id": sample_id,
        "dataset_label": dataset_label, "status": "passed_positional_checks",
        "name_convention": convention, "quality_encoding": quality_encoding,
        "metrics": metrics, "inputs": inputs,
        "scope": "Equal read counts and matching normalized identifiers in input order, with explicit mate labels. No uniqueness, sequence-orientation, alignment, or biological-identity validation.",
    }
    markdown = (
        "# Paired FASTQ consistency summary\n\n"
        f"Dataset label supplied by the caller: {dataset_label}\n\n"
        f"Sample **{sample_id}** passed positional checks for **{metrics['validated_pairs']} pairs** using the **{convention}** naming convention. "
        "The two files have equal numbers of fully parsed records, matching normalized identifiers in the same order, and the expected mate labels.\n\n"
        "This is a file-consistency result. It does not demonstrate biological pairing, unique identifiers, correct orientation, correct organism, sequence accuracy, or successful alignment. "
        "Read sequences were not compared, reverse-complemented, repaired, reordered, trimmed, or filtered.\n\n"
        "The public ERR458493 example elsewhere in this repository is single-end and is not used as paired-end evidence.\n"
    )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pair_check_", dir=output_dir.parent) as directory:
        staging = Path(directory)
        (staging / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (staging / "report.md").write_text(markdown, encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            os.replace(staging / name, output_dir / name)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read1", type=Path, required=True)
    parser.add_argument("--read2", type=Path, required=True)
    parser.add_argument("--name-convention", choices=("suffix", "illumina"), required=True)
    parser.add_argument("--quality-encoding", choices=("phred33",), required=True)
    parser.add_argument("--sample-id", default="sample")
    parser.add_argument("--dataset-label", default="User-supplied reads; biological pairing not independently verified")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run(args.read1, args.read2, args.output_dir, args.name_convention, args.quality_encoding, args.sample_id, args.dataset_label)
    except (ValidationError, OSError, UnicodeError, EOFError, zlib.error) as error:
        print(f"Pair-validation error: {error}", file=sys.stderr)
        return 2
    print(f"Validated {report['metrics']['validated_pairs']} positional read pairs; wrote {args.output_dir / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
