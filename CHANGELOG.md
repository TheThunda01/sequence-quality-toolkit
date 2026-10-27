# Changelog

## Unreleased — October 27, 2026

- Added optional reproducible SVG/PNG views pairing per-cycle mean quality with contributing-read counts, using saved public and synthetic summaries.
- Reject mismatched cycle identities, denominators, nonfinite quality values, and inconsistent weighted means before plotting. Core QC remains standard-library-only.
- Preserve the two plotted report JSON files byte-for-byte on Windows so figure provenance matches the repository inputs.

## 0.3.0

- Added a separate paired FASTQ consistency validator with explicit suffix/Illumina name rules, raw-input hashes, and synthetic examples.
- Added biology/concepts documentation and a source-backed comparison of relevant SeqKit and seqtk behavior.
- Preserved the public yeast example's single-end label; no paired biological data or strand assumptions were introduced.

## 0.2.0

- Added a streaming FASTQ workflow with explicit Phred+33, plain/gzip input, per-read/per-cycle metrics, length distributions, and raw-byte fingerprints.
- Added a checksum-verified 1,000-read public yeast example, source attribution, and optional retrieval/rebuild script.
- Added synthetic FASTQ cases and tests for malformed records, compression, encoding bounds, deterministic reports, and failed-run preservation.
- Added per-sample FASTA summaries, retaining the existing pooled and per-record outputs.

## 0.1.0

- Initial FASTA and manifest checks, synthetic fixtures, explicit metric definitions, and reproducible reports.
