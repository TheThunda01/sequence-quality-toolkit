# Data dictionary

## Inputs

| File/field | Meaning | Validation |
| --- | --- | --- |
| FASTA identifier | First whitespace-delimited token after `>`. | Unique, nonempty, restricted identifier characters. Descriptions are ignored. |
| FASTA sequence | Concatenated nonblank sequence lines. | Nonempty; DNA IUPAC subset `ACGTRYSWKMBDHVN`; lowercase converted to uppercase. |
| `sequence_id` | FASTA identifier in the manifest. | Exactly one row for each FASTA record. |
| `sample_id` | User-assigned grouping label. | Required; same character contract as identifiers. Not a verified biological identity. |

## Per-sequence output

| Field | Type and definition |
| --- | --- |
| `sequence_id`, `sample_id` | Input identifiers. |
| `length` | Integer count of all accepted sequence symbols. |
| `canonical_bases` | Integer count of A, C, G, and T. |
| `gc_fraction` | `(G + C) / (A + C + G + T)`, rounded to six decimals. JSON `null` / CSV blank when denominator is zero. |
| `ambiguous_bases` | Count of R, Y, S, W, K, M, B, D, H, V, and N. |
| `ambiguous_fraction` | `ambiguous_bases / length`, rounded to six decimals. |
| `n_bases` | Count of N alone; a subset of `ambiguous_bases`. |

## JSON summary and provenance

`sequence_count` counts FASTA records; `sample_count` counts distinct manifest sample labels. `total_bases`, `canonical_bases`, and `ambiguous_bases` pool counts across records. Pooled fractions use the pooled counts, not the mean of per-record fractions. `symbol_counts` contains every accepted uppercase symbol, including zero counts. `length_n50` is the first record length at which the longest-first cumulative sum reaches at least half the pooled total. It is descriptive, and does not imply that records belong to one assembly.

`inputs` contains the two input basenames and SHA-256 digests of their bytes, including line endings. `dataset_label` is the caller's text, not a label inferred or independently verified by the tool. `schema_version` identifies the report format; `tool_version` identifies the implementation. Reports omit timestamps and absolute paths so the same inputs and label produce identical report bytes in the supported environment.

Identifiers are exported as text. Even with the restricted character set, consumers should import identifier columns as text to preserve leading zeros or values that spreadsheet software may interpret as dates.
