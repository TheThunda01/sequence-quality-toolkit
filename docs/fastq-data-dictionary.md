# FASTQ data dictionary

FASTQ stores a sequence and one encoded quality score per position. A manifest declares the input files and labels. See the [glossary](glossary.md) for Phred, GC, JSON, and other terms.

## Manifest

| Field | Rule |
| --- | --- |
| `sample_id` | Unique file label. Starts with a letter/digit; remaining characters may be letters, digits, `_`, `.`, `:`, or `-`. This is not an inferred biological identity. |
| `fastq_path` | Existing plain/gzip file, relative to the manifest or absolute. The same resolved file cannot appear twice. |
| `quality_encoding` | Exactly `phred33`. Required, never inferred. |

One file per row is supported by the quality-summary command. Separate mate files are treated as independent files with distinct labels. Use the separate [paired-file validator](paired-fastq.md) for supported positional identifier checks.

## Sample and read fields

| Field | Definition |
| --- | --- |
| `read_count` | Number of fully parsed FASTQ records. Empty files fail. |
| `total_bases` | Number of accepted DNA symbols, including ambiguity symbols. |
| `min_length`, `max_length`, `mean_length` | Read-length summaries. Mean is weighted equally by reads. |
| `canonical_bases` | Count of A, C, G, T. |
| `ambiguous_bases`, `n_bases` | Non-ACGT accepted symbols; N alone is a subset. |
| `gc_fraction` | $`\frac{G+C}{A+C+G+T}`$, excluding all ambiguity symbols. `null` in JSON / blank in CSV if undefined. |
| `ambiguous_fraction`, `n_fraction` | Relevant symbol count divided by all accepted symbols. |
| `base_weighted_mean_phred` | Sum of all Q scores divided by all sequence symbols. |
| `q20_fraction`, `q30_fraction` | Fraction of symbols with Q≥20 or Q≥30. Thresholds are descriptive. |
| `mean_expected_errors_per_read` | Sum of 10^(−Q/10) over all bases, divided by read count. An estimate implied by quality scores, not observed errors. |
| `quality_histogram` | JSON object mapping exact integer Q scores to counts. |
| `symbol_counts` | JSON counts of every accepted DNA symbol. |
| `input_sha256`, `input_bytes` | Fingerprint and length of raw input file bytes, including gzip compression when present. |
| `input_name` | Input basename. Absolute paths are omitted from reports. |
| `read_index` | One-based input order within that file. |
| `read_id` | First token after `@`, recorded in JSON Lines without spreadsheet interpretation. IDs need not be unique. |
| `mean_phred`, `min_phred` | Per-read Q summaries. |
| `expected_errors_from_qualities` | Per-read sum of implied error probabilities. |

`read_metrics.jsonl` contains one object per read with its sample label. It includes length, GC, canonical/ambiguous/N counts, mean/minimum Q, Q20/Q30 fractions, and expected errors. The full sequences and quality strings are not copied into reports. Fractions and mean scores are rounded to six decimal places; expected-error fields to eight. Aggregates use original integer counts, not rounded read-level values.

`cycles.csv` uses one-based `cycle`; `observed_bases` is the number of reads reaching that position. Its means/fractions use that denominator. `length_distribution.csv` has one row for each observed `(sample_id, length)` pair and its `read_count`.

CSV exports prefix formula-like text with an apostrophe when it begins with `=`, `+`, `-`, or `@`, including after leading whitespace or a byte-order mark. This affects exported text such as an input filename; numeric values and blank fields keep their existing representation. JSON, JSON Lines, input files, and input-lock provenance retain the original values.

## Report provenance

`report.json` records the manifest's byte hash, tool/schema versions, input raw-byte hashes, the caller's `dataset_label`, and the read-length limit. It has no timestamp, keeping repeated local runs byte-reproducible. The label is supplied by the caller and is not verified by the tool. Dataset-specific source attribution belongs in a provenance file, as in `examples/public/provenance.json`.
