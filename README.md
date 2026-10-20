# Sequence Quality Toolkit

Small file checks are easy to overlook. This Python command checks that a DNA FASTA and its sample manifest agree, then produces a compact report of sequence lengths and symbols. It is a worked software project: the included sequences are deliberately simple synthetic strings, not observations from an organism.

**Status:** working educational tool, version 0.1.0. No third-party dependencies, no network requests, and no biological prediction.

## What it demonstrates

- A strict parser with useful errors for duplicate IDs, empty sequences, and unsupported symbols.
- Manifest reconciliation before analysis, so a missing sample mapping cannot silently disappear.
- Explicit metric definitions, machine-readable outputs, and input fingerprints.
- Tests for the edge cases that can change an interpretation, including zero GC denominators and the N50 half-length boundary.

## Run the example

Use Python **3.12**. From this repository's root:

```sh
python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir reports --dataset-label "Synthetic teaching fixture; not observed biological data"
python -m unittest discover -s tests -v
```

On systems where Python is called `python3`, substitute `python3`. No installation is needed. `make demo` and `make test` are shortcuts if Make is available.

The command writes three files, replacing earlier outputs with those names in the chosen directory:

| Output | What is in it |
| --- | --- |
| [reports/report.md](reports/report.md) | A short human-readable summary. |
| [reports/sequences.csv](reports/sequences.csv) | One row per sequence, including its sample label. |
| [reports/report.json](reports/report.json) | Dataset totals, symbol counts, definitions through field names, and SHA-256 input fingerprints. |

The bundled example has **3 records, 42 symbols, and 10 ambiguous symbols**. Its pooled GC fraction is **0.5** when the denominator includes only A, C, G, and T. The all-ambiguous record has a blank GC value in CSV and `null` in JSON. That value is undefined, not zero. The pooled length N50 is **24 symbols**.

To see a deliberate validation failure:

```sh
python sequence_qc.py --fasta examples/invalid_duplicate.fasta --manifest examples/manifest.csv --output-dir tmp/invalid
```

This exits with status 2 and reports a duplicate identifier. Input validation completes before any outputs are written. Existing reports are not removed on failure, so check the command's exit status rather than assuming an old report came from the latest run.

## Input contract

The FASTA can contain lowercase letters, wrapped sequences, blank lines, and descriptions after an identifier. IDs must start with a letter or digit; remaining characters can be letters, digits, `_`, `.`, `:`, or `-`. IDs are case-sensitive. Sequence symbols are normalized to uppercase. This intentionally limited DNA parser accepts `ACGTRYSWKMBDHVN` and rejects RNA `U`, gaps, digits, and spaces within a sequence line. See the [methods](docs/methods.md) for the code reference and choices.

The manifest has exactly these two columns, in this order:

```csv
sequence_id,sample_id
toy_alpha,toy_sample_1
toy_beta,toy_sample_1
```

Every FASTA ID must appear exactly once in the manifest, with no extra manifest IDs. Several sequences may map to one sample. Sample IDs follow the same character rules as sequence IDs. Full field definitions are in the [data dictionary](docs/data-dictionary.md).

## What the report can tell us

It can tell us whether files satisfy this input contract and what symbols and lengths they contain. N50 is a length-distribution statistic: records at least that long account for at least half the total length. Here, records are pooled across sample labels, so the example's N50 is **not** an assembly-quality result for either sample. [NCBI's definition](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/) supplies the length-statistic convention; this tool does not assemble reads.

These summaries cannot establish organism identity, contamination, sequence accuracy, biological function, or assembly correctness. A passing report means only that these checks passed. There is no universal GC or N50 threshold for declaring an arbitrary input good.

## Provenance and reuse

All example inputs were written for this project. They are repeated or ambiguity-only text strings with no accession, sampling event, or claimed biological origin. Code and project-created fixtures are covered by the repository's MIT license. No external sequence dataset is distributed. The [methods and sources](docs/methods.md) distinguish published definitions from implementation choices.

The next useful extension would be a streaming reader for large files and per-sample length summaries, with the same explicit definitions. Neither is implemented in this version.
