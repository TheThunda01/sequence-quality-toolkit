"""Small, strict DNA FASTA and manifest checks. Standard library only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

__version__ = "0.1.0"
ALPHABET = frozenset("ACGTRYSWKMBDHVN")
CANONICAL = frozenset("ACGT")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*\Z")


class ValidationError(ValueError):
    """Input violates the documented format; no report should be produced."""


@dataclass(frozen=True)
class SequenceRecord:
    sequence_id: str
    sequence: str


def valid_identifier(value: str, context: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{context}: use letters/digits followed by letters/digits, _, ., :, or -")


def parse_fasta(handle: TextIO) -> list[SequenceRecord]:
    """Read wrapped DNA FASTA, preserving record order and normalizing case."""
    records: list[SequenceRecord] = []
    seen: set[str] = set()
    identifier: str | None = None
    pieces: list[str] = []

    def finish() -> None:
        if identifier is not None:
            sequence = "".join(pieces)
            if not sequence:
                raise ValidationError(f"FASTA record {identifier!r} has no sequence")
            records.append(SequenceRecord(identifier, sequence))

    for line_number, raw in enumerate(handle, 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            finish()
            header = line[1:].strip()
            if not header:
                raise ValidationError(f"FASTA line {line_number}: empty header")
            identifier = header.split()[0]
            valid_identifier(identifier, f"FASTA line {line_number} identifier")
            if identifier in seen:
                raise ValidationError(f"FASTA line {line_number}: duplicate identifier {identifier!r}")
            seen.add(identifier)
            pieces = []
        else:
            if identifier is None:
                raise ValidationError(f"FASTA line {line_number}: sequence precedes the first header")
            sequence = line.upper()
            invalid = sorted(set(sequence) - ALPHABET)
            if invalid:
                raise ValidationError(f"FASTA line {line_number}: invalid DNA characters {invalid!r}")
            pieces.append(sequence)
    finish()
    if not records:
        raise ValidationError("FASTA has no sequence records")
    return records


def parse_manifest(handle: TextIO) -> dict[str, str]:
    """Read a strict two-column CSV mapping each sequence to a sample."""
    reader = csv.DictReader(handle, strict=True)
    if reader.fieldnames != ["sequence_id", "sample_id"]:
        raise ValidationError("Manifest header must be exactly sequence_id,sample_id")
    manifest: dict[str, str] = {}
    for line_number, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValidationError(f"Manifest line {line_number}: expected two columns")
        sequence_id, sample_id = row["sequence_id"], row["sample_id"]
        valid_identifier(sequence_id, f"Manifest line {line_number} sequence_id")
        valid_identifier(sample_id, f"Manifest line {line_number} sample_id")
        if sequence_id in manifest:
            raise ValidationError(f"Manifest line {line_number}: duplicate sequence_id {sequence_id!r}")
        manifest[sequence_id] = sample_id
    if not manifest:
        raise ValidationError("Manifest has no data rows")
    return manifest


def reconcile(records: list[SequenceRecord], manifest: dict[str, str]) -> None:
    identifiers = {record.sequence_id for record in records}
    missing = sorted(identifiers - manifest.keys())
    extra = sorted(manifest.keys() - identifiers)
    if missing or extra:
        raise ValidationError(f"Manifest mismatch: missing sequence IDs {missing}; extra sequence IDs {extra}")


def length_n50(lengths: list[int]) -> int:
    """Length at which longest-first cumulative length reaches at least half."""
    if not lengths or any(isinstance(length, bool) or not isinstance(length, int) or length <= 0 for length in lengths):
        raise ValidationError("N50 needs a nonempty list of positive integer lengths")
    total = sum(lengths)
    cumulative = 0
    for length in sorted(lengths, reverse=True):
        cumulative += length
        if 2 * cumulative >= total:
            return length
    raise AssertionError("Unreachable for positive lengths")


def fraction(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def summarize(records: list[SequenceRecord], manifest: dict[str, str]) -> dict:
    reconcile(records, manifest)
    rows = []
    all_counts: Counter[str] = Counter()
    for record in records:
        counts = Counter(record.sequence)
        all_counts.update(counts)
        canonical = sum(counts[base] for base in CANONICAL)
        ambiguous = len(record.sequence) - canonical
        rows.append({
            "sequence_id": record.sequence_id,
            "sample_id": manifest[record.sequence_id],
            "length": len(record.sequence),
            "canonical_bases": canonical,
            "gc_fraction": fraction(counts["G"] + counts["C"], canonical),
            "ambiguous_bases": ambiguous,
            "ambiguous_fraction": fraction(ambiguous, len(record.sequence)),
            "n_bases": counts["N"],
        })
    total = sum(row["length"] for row in rows)
    canonical = sum(all_counts[base] for base in CANONICAL)
    return {
        "sequence_count": len(rows),
        "sample_count": len(set(manifest.values())),
        "total_bases": total,
        "canonical_bases": canonical,
        "ambiguous_bases": total - canonical,
        "gc_fraction": fraction(all_counts["G"] + all_counts["C"], canonical),
        "ambiguous_fraction": fraction(total - canonical, total),
        "length_n50": length_n50([row["length"] for row in rows]),
        "symbol_counts": {base: all_counts[base] for base in sorted(ALPHABET)},
        "sequences": rows,
    }


def file_provenance(path: Path, contents: bytes | None = None) -> dict[str, str]:
    data = path.read_bytes() if contents is None else contents
    return {"name": path.name, "sha256": hashlib.sha256(data).hexdigest()}


def build_report(fasta: Path, manifest_path: Path, dataset_label: str) -> dict:
    # Parse and fingerprint the same bytes, even if a file changes later.
    fasta_bytes = fasta.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    records = parse_fasta(io.StringIO(fasta_bytes.decode("utf-8")))
    manifest = parse_manifest(io.StringIO(manifest_bytes.decode("utf-8"), newline=""))
    return {
        "schema_version": "1.0",
        "tool_version": __version__,
        "dataset_label": dataset_label,
        "scope": "Descriptive DNA file checks; biological source and sequence accuracy are not verified.",
        "inputs": {"fasta": file_provenance(fasta, fasta_bytes), "manifest": file_provenance(manifest_path, manifest_bytes)},
        "metrics": summarize(records, manifest),
    }


def markdown_report(report: dict) -> str:
    m = report["metrics"]
    gc = "undefined (no A/C/G/T bases)" if m["gc_fraction"] is None else f"{m['gc_fraction']:.6f}"
    return (
        "# Sequence file summary\n\n"
        f"Dataset label supplied by the caller: {report['dataset_label']}\n\n"
        f"- Sequences: **{m['sequence_count']}** across **{m['sample_count']}** sample labels.\n"
        f"- Total symbols: **{m['total_bases']}**; ambiguous symbols: **{m['ambiguous_bases']}**.\n"
        f"- GC fraction among A/C/G/T symbols: **{gc}**.\n"
        f"- Length N50 across all input records: **{m['length_n50']} symbols**.\n\n"
        "GC uses only A, C, G, and T in its denominator. Ambiguity includes N and the other accepted IUPAC ambiguity symbols.\n\n"
        "These are descriptive checks, not evidence of organism identity, contamination, sequence accuracy, biological function, or assembly correctness. "
        "The length statistic pools the supplied records; if they belong to different samples, it is not an assembly statistic for any one sample.\n\n"
        "See `sequences.csv` for per-record values and `report.json` for input SHA-256 fingerprints, symbol counts, and machine-readable results.\n"
    )


def write_report(report: dict, output_dir: Path, input_paths: list[Path]) -> None:
    outputs = [output_dir / name for name in ("report.json", "sequences.csv", "report.md")]
    if {path.resolve() for path in input_paths} & {path.resolve() for path in outputs}:
        raise ValidationError("An output path would overwrite an input file")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    rows = report["metrics"]["sequences"]
    with outputs[1].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    outputs[2].write_text(markdown_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-label", default="Unspecified input; source not independently verified")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.fasta, args.manifest, args.dataset_label)
        write_report(report, args.output_dir, [args.fasta, args.manifest])
    except (ValidationError, OSError, UnicodeError, csv.Error) as error:
        print(f"Input/output error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output_dir / 'report.json'} ({report['metrics']['sequence_count']} sequences)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
