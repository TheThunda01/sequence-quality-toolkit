# Sequence Quality Toolkit

This project asks a practical question: **what can we learn from sequence files before doing biological analysis?** It checks FASTA records against a manifest and summarizes raw FASTQ quality scores without changing the reads. The code is small enough to follow, with tests for details that can quietly change a result.

**[Project context: background, purpose, and key themes](docs/project-context.md)**

**[Biology and concepts: reads, quality scores, pairs, and interpretation](docs/biology-and-concepts.md)**

**Version 0.3.0:** working educational software with a real public yeast RNA-seq example and deliberately imperfect synthetic fixtures. Python 3.12; standard library only; no network access during QC.

## Why this project

Small file-handling decisions can change what a sequence summary means. This project makes input contracts and metric definitions visible, using a public excerpt and deliberately imperfect synthetic examples.

## What it does

### FASTQ quality summaries

- Streams plain-text or gzip files, including wrapped sequence and quality lines.
- Requires an explicit `phred33` declaration instead of guessing the quality encoding.
- Checks headers, separators, DNA symbols, sequence/quality length agreement, and printable quality bounds.
- Writes per-read metrics as JSON Lines while retaining summary counters in memory.
- Produces per-sample and per-cycle quality summaries, exact read-length distributions, N/ambiguity counts, and raw-input SHA-256 fingerprints.
- Validates every sample before replacing reports, so a malformed later file does not replace an earlier valid report set.

The [synthetic example](reports/fastq_synthetic/report.md) makes low-quality scores and variable lengths easier to see:

```sh
python fastq_qc.py --manifest examples/fastq/samples.csv --output-dir reports/fastq_synthetic --dataset-label "Synthetic test reads; no biological origin"
```

Each FASTQ manifest row identifies **one file**, with paths relative to the manifest:

```csv
sample_id,fastq_path,quality_encoding
sample_A,sample_A.fastq.gz,phred33
sample_B,sample_B.fastq,phred33
```

Sample IDs and resolved input paths must be unique. This quality-summary command analyzes each file independently and does not merge lanes. Use the separate paired-file check below for positional mate consistency. Quality scores that could fit more than one encoding remain the caller's responsibility. Detailed input rules and metric definitions are in the [FASTQ methods](docs/fastq-methods.md) and [data dictionary](docs/fastq-data-dictionary.md).

| Output in the chosen directory | Contents |
| --- | --- |
| `report.md` | Readable summary and interpretation boundaries. |
| `report.json` | Provenance, per-sample statistics, and quality/symbol histograms. |
| `samples.csv` | One row per manifest file. |
| `cycles.csv` | Per-position summaries, using only reads that reach each position. |
| `length_distribution.csv` | Exact counts of reads at each length. |
| `read_metrics.jsonl` | One JSON object per read; this can be large for complete runs. |

### FASTA and manifest checks

The original workflow remains available, now with separate sample summaries:

```sh
python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir reports --dataset-label "Synthetic teaching fixture; not observed biological data"
```

This checks duplicate or empty records, unsupported DNA symbols, and missing/extra manifest IDs. It reports sequence lengths, GC with an explicit denominator, ambiguity counts, and pooled **and per-sample** length N50. The included FASTA is synthetic: 3 records, 42 symbols, 10 ambiguous symbols. GC is `null` when no A/C/G/T bases are available; it is never silently set to zero.

See the [FASTA report](reports/report.md), [methods](docs/methods.md), and [dictionary](docs/data-dictionary.md). N50 here describes supplied sequence lengths. It does not validate an assembly, and the pooled statistic across unrelated samples is not an assembly-quality measure.

### Paired-file consistency

The separate paired FASTQ validator checks equal read counts, matching normalized identifiers in the same order, and explicit R1/R2 mate labels. It accepts plain/gzip input and requires you to select one supported naming convention.

```sh
python paired_fastq_check.py --read1 examples/paired/suffix_R1.fastq --read2 examples/paired/suffix_R2.fastq --name-convention suffix --quality-encoding phred33 --sample-id synthetic_suffix --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir reports/paired_suffix
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

## Example results

The repository includes the first **1,000 reads** from [ENA run ERR458493](https://www.ebi.ac.uk/ena/browser/view/ERR458493), part of the *Saccharomyces cerevisiae* study [PRJEB5348](https://www.ncbi.nlm.nih.gov/bioproject/PRJEB5348). The complete source download was verified against its archive MD5 before the subset was created. Selection, checksums, source links, and reuse terms are in [public-data provenance](docs/public-data.md).

From the repository root, run:

```sh
python fastq_qc.py --manifest examples/public/samples.csv --output-dir reports/fastq_public --dataset-label "First 1000 archived reads of yeast RNA-seq run ERR458493; convenience prefix, not representative"
python -m unittest discover -s tests -v
```

Use `python3` if that is your Python command. No installation or download is needed for this example. You can inspect the checked-in [report](reports/fastq_public/report.md) before running anything.

| Result from the included subset | Value |
| --- | ---: |
| Reads | 1,000 |
| Read length | 51 symbols for every read |
| Total symbols | 51,000 |
| N symbols | 2 |
| Mean Phred score, weighted by bases | 37.015059 |
| Fraction of bases with Phred score ≥30 | 0.944373 |

These values describe this small prefix. **They are not a quality assessment of the complete run, a measure of observed sequencing errors, or evidence for a biological effect.** We use the archive's organism label; the tool does not verify identity or contamination. The study publication is credited in the provenance guide, but its differential-expression analysis is not reproduced here.

## Practical use and limitations

The toolkit does not trim or filter reads, identify adapters, inspect duplication or overrepresented sequences, calculate mapping quality, assess contamination, or infer function. There is no automatic pass/fail quality threshold. [FastQC, fastp, and MultiQC](docs/fastq-methods.md#relationship-to-established-tools) cover broader tasks and have their own methods and assumptions. This repository is an inspectable subset of QC calculations, not a replacement or a claimed reimplementation of those tools.

Project code and synthetic fixtures use the MIT license. The public sequencing subset retains its [ENA/INSDC data-sharing terms](docs/public-data.md#reuse-and-attribution); it is not relicensed as project code. The initial implementation used AI assistance, as described in [CONTRIBUTING.md](CONTRIBUTING.md).

The [practical-use guide](docs/practical-use.md) explains how to transfer and verify an input lock. A lock records the bytes chosen by the operator; it cannot authenticate their source or establish quality. Keep the public yeast prefix and synthetic paired fixtures distinct.

### Integrated input check

The optional `--input-lock` flag now enforces the declared fingerprints within QC and checks the raw bytes actually consumed before publishing reports. Without the flag, earlier behavior is preserved. It does not authenticate sample identity or prevent concurrent filesystem changes; see the [updated contract](docs/practical-use.md).

## Documentation

| Guide | Purpose |
| --- | --- |
| [Project context](docs/project-context.md) | Background and key questions |
| [Biology and concepts](docs/biology-and-concepts.md) | Reads, quality scores, pairing, and interpretation |
| [FASTA methods](docs/methods.md) / [FASTQ methods](docs/fastq-methods.md) | Exact contracts and calculations |
| [Paired-file methods](docs/paired-fastq.md) | Supported naming conventions and limits |
| [References and related tools](docs/related-tools.md) | Attribution and relationship to other software |
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

`make demo` regenerates all five report sets without downloading data. GitHub Actions runs the tests and verifies that regenerated reports match the committed results. To rebuild the public subset itself, use [the documented retrieval script](docs/public-data.md); that optional step downloads about 60 MB and validates the complete archive before extracting 1,000 reads.

The input-lock format has schema version 1.0. Existing scientific reports and toolkit calculation versions are retained. `make audit` checks the public input lock. See [CONTRIBUTING.md](CONTRIBUTING.md) for contributions and implementation provenance.
