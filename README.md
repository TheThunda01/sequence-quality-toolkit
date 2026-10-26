# Sequence Quality Toolkit

Sequence Quality Toolkit checks sequence files and summarizes their quality scores before biological analysis. It checks FASTA records (sequences and headers) against a manifest of expected records and separately summarizes FASTQ files, which add a quality score at each position. It leaves reads unchanged. Tests cover file-handling details that can alter a result.

**[Project context: background, purpose, and key themes](docs/project-context.md)**

**[Biology and concepts: reads, quality scores, pairs, and interpretation](docs/biology-and-concepts.md)**

**Version 0.3.0:** working educational software with a real public yeast RNA-sequencing (RNA-seq) example and deliberately imperfect synthetic fixtures. Python 3.12; standard library only; no network access during QC.

## Why this project

File-handling decisions affect sequence summaries. Using a public excerpt and deliberately imperfect synthetic examples, this project shows exactly which inputs each check accepts and how it calculates each metric.

## What it does

### FASTQ quality summaries

- Streams plain-text or gzip files, including wrapped sequence and quality lines.
- Requires an explicit `phred33` declaration (quality characters encode the score plus 33) instead of guessing the quality encoding.
- Checks headers, separators, DNA symbols, sequence/quality length agreement, and printable quality bounds.
- Writes per-read metrics as JSON Lines (one structured text object per line) while retaining summary counters in memory.
- Produces per-sample and per-cycle quality summaries, exact read-length distributions, N/ambiguity counts, and raw-input SHA-256 fingerprints (identifiers calculated from exact file bytes).
- Validates every sample before replacing reports, so a malformed later file does not replace an earlier valid report set.

The [synthetic example](reports/fastq_synthetic/report.md) makes low-quality scores and variable lengths easier to see:

```sh
python fastq_qc.py --manifest examples/fastq/samples.csv --output-dir my-qc-synthetic --dataset-label "Synthetic test reads; no biological origin"
```

Each row of the FASTQ manifest identifies **one file**. Paths are relative to the manifest:

```csv
sample_id,fastq_path,quality_encoding
sample_A,sample_A.fastq.gz,phred33
sample_B,sample_B.fastq,phred33
```

Sample IDs and resolved input paths must be unique. The quality-summary command analyzes each file independently and does not merge lanes. To check whether paired records match in order, use the separate paired-file check below. The caller must choose the correct quality encoding, even when scores could fit more than one encoding. See the [FASTQ methods](docs/fastq-methods.md) and [data dictionary](docs/fastq-data-dictionary.md) for input rules and metric definitions.

| Output in the chosen directory | Contents |
| --- | --- |
| `report.md` | Readable summary and interpretation boundaries. |
| `report.json` | Provenance, per-sample statistics, and quality/symbol histograms. |
| `samples.csv` | One row per manifest file. |
| `cycles.csv` | Per-position summaries, using only reads that reach each position. |
| `length_distribution.csv` | Exact counts of reads at each length. |
| `read_metrics.jsonl` | One JSON object per read; this can be large for complete runs. |

### FASTA and manifest checks

The FASTA workflow reports both pooled and per-sample summaries:

```sh
python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir my-fasta-qc --dataset-label "Synthetic teaching fixture; not observed biological data"
```

This checks duplicate or empty records, unsupported DNA symbols, and missing/extra manifest IDs. It reports sequence lengths, GC fraction, $`\frac{G+C}{A+C+G+T}`$, with an explicit denominator, ambiguity counts, and pooled **and per-sample** length N50, the record length reached when longest-first records cover at least half the total length. The included FASTA is synthetic: 3 records, 42 symbols, 10 ambiguous symbols. GC is `null` when no A/C/G/T bases are available; it is never silently set to zero.

See the [FASTA report](reports/report.md), [methods](docs/methods.md), and [dictionary](docs/data-dictionary.md). N50 here describes supplied sequence lengths. It does not validate an assembly, and the pooled statistic across unrelated samples is not an assembly-quality measure.

### Paired-file consistency

The paired FASTQ validator checks that files have equal read counts, normalized identifiers match in order, and headers contain explicit R1/R2 mate labels. It accepts plain or gzip input and requires one supported naming convention.

```sh
python paired_fastq_check.py --read1 examples/paired/suffix_R1.fastq --read2 examples/paired/suffix_R2.fastq --name-convention suffix --quality-encoding phred33 --sample-id synthetic_suffix --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir my-paired-qc
```

See the [paired-file rules](docs/paired-fastq.md), [example result](reports/paired_suffix/report.md), and [related GitHub tools](docs/related-tools.md). It does not reorder reads, assume reverse-complement relationships, or establish biological pairing. The public yeast excerpt is single-end; paired examples are explicitly synthetic.

### Input fingerprints

`input_fingerprints.py` creates and verifies a separate lock for the exact FASTQ sample sheet and raw input bytes. It detects file changes before QC without claiming the content is valid FASTQ or biologically identified.

## Quick start

Python 3.12 and the standard library are sufficient. From the repository root:

```sh
python fastq_qc.py --manifest examples/public/samples.csv --input-lock examples/public/input-lock.json --output-dir my-qc --dataset-label "First 1000 archived reads of ERR458493; convenience prefix, not representative"
python -m unittest discover -s tests -v
```

The analysis examples above and the quick start write fresh results to `my-*` directories, preserving the committed examples under `reports/`. Use a new output directory for another run; existing report files in the chosen directory are replaced after validation.

## Example results

The repository includes the first **1,000 reads** from [ENA run ERR458493](https://www.ebi.ac.uk/ena/browser/view/ERR458493), part of the *Saccharomyces cerevisiae* study [PRJEB5348](https://www.ncbi.nlm.nih.gov/bioproject/PRJEB5348). The complete source download was verified against its archive MD5 before the subset was created. Selection, checksums, source links, and reuse terms are in [public-data provenance](docs/public-data.md).

The quick start above verifies the included input lock and writes this analysis to `my-qc/`. Use `python3` if that is your Python command. No third-party installation or download is needed for this example. You can inspect the checked-in [report](reports/fastq_public/report.md) before running anything.

| Result from the included subset | Value |
| --- | ---: |
| Reads | 1,000 |
| Read length | 51 symbols for every read |
| Total symbols | 51,000 |
| N symbols | 2 |
| Mean Phred score, weighted by bases | 37.015059 |
| Fraction of bases with Phred score ≥30 | 0.944373 |

These values describe only this small prefix. **They do not assess the complete run, measure observed sequencing errors, or establish a biological effect.** The tool uses the archive's organism label without verifying identity or contamination. The provenance guide credits the study publication; this project does not reproduce its differential-expression analysis.

## Practical use and limitations

The toolkit does not trim or filter reads, identify adapters, inspect duplication or overrepresented sequences, calculate mapping quality, assess contamination, or infer function. There is no automatic pass/fail quality threshold. [FastQC, fastp, and MultiQC](docs/fastq-methods.md#relationship-to-established-tools) cover broader tasks and have their own methods and assumptions. This repository is an inspectable subset of QC calculations, not a replacement or a claimed reimplementation of those tools.

Project code and synthetic fixtures use the MIT license. The public sequencing subset retains its [ENA/INSDC data-sharing terms](docs/public-data.md#reuse-and-attribution); it is not relicensed as project code. The initial implementation used AI assistance, as described in [CONTRIBUTING.md](CONTRIBUTING.md).

The [practical-use guide](docs/practical-use.md) explains how to transfer and verify an input lock. A lock records the bytes chosen by the operator; it cannot authenticate their source or establish quality. Keep the public yeast prefix and synthetic paired fixtures distinct.

### Integrated input check

With `--input-lock`, QC verifies the declared fingerprints and checks the raw bytes it reads before publishing reports. Omitting the flag preserves the existing behavior. The check does not authenticate sample identity or prevent concurrent filesystem changes; see the [updated contract](docs/practical-use.md).

## Documentation

| Guide | Purpose |
| --- | --- |
| [Project context](docs/project-context.md) | Background and key questions |
| [Biology and concepts](docs/biology-and-concepts.md) | Reads, quality scores, pairing, and interpretation |
| [FASTA methods](docs/methods.md) / [FASTQ methods](docs/fastq-methods.md) | Exact contracts and calculations |
| [Paired-file methods](docs/paired-fastq.md) | Supported naming conventions and limits |
| [References](docs/references.md) / [related tools](docs/related-tools.md) | Complete bibliography and relationship to other software |
| [Glossary](docs/glossary.md) | Biological, statistical, and computing vocabulary |
| [Assumptions](docs/assumptions.md) | Rationale, checks, and consequences of material assumptions |
| [Reference audit](docs/reference-audit.json) | Source-by-source verification and access limits |
| [Scientific and editorial review](docs/review-2026-10-20.md) | Corrections, coverage, and verification results |
| [Maintenance and source review](docs/review-2026-10-21.md) | Current fixes, source checks, validation, and remaining limits |
| [Public-data provenance](docs/public-data.md) | Source, extraction, checksums, and reuse terms |
| [Practical use](docs/practical-use.md) | Input locks, worked use case, and next improvements |
| [Literature review](docs/literature-review.md) | Bounded review supporting this extension |
| [Search log](docs/search-log.json) | Exact queries, counts, identifiers, and decisions |
| [Evidence update 02](docs/search-update-02.json) | Targeted same-day follow-up search and decisions |

## Development and reuse

```sh
make test
make demo
```

`make demo` intentionally regenerates all five committed report sets under `reports/` without downloading data. The GitHub Actions workflow specifies continuous integration checks that run the tests and verify that regenerated reports match the committed results. To rebuild the public subset itself, use [the documented retrieval script](docs/public-data.md); that optional step downloads about 60 MB and validates the complete archive before extracting 1,000 reads.

The input-lock format has schema version 1.0. Existing scientific reports and toolkit calculation versions are retained. `make audit` checks the public input lock. See [CONTRIBUTING.md](CONTRIBUTING.md) for contributions and implementation provenance.
