# Rapid literature and practice review

## Question and scope

Which small reliability improvement helps users carry an input identity from file receipt to a FASTQ QC run, while keeping byte integrity, format validation, and biological interpretation distinct? The review focused on file contracts and reporting. It did not compare aligners, establish assay-specific acceptance thresholds, or assess clinical use.

### Round 2 update — 2026-10-20

This same-day follow-up asks how to enforce the existing input lock inside the actual QC run, before staged results replace an older report. It is a new implementation scope on 2026-10-20, not an elapsed-time literature update.

## Search record

Search date: **2026-10-20**. Exact queries, date restrictions, pagination limits, identifiers, and decisions are in [search-log.json](search-log.json). A recent broad PubMed query returned 14 records; the first 10, sorted by publication date, were screened. Four later records were not retrieved. A narrow `fastp[Title] OR fastplong[Title]` query returned two records, both inspected. The two pages contained 12 distinct records. A foundational known-title search returned zero; the known PMID was retrieved directly instead.

Two recent software papers were retained from the narrow search. The foundational FASTQ article was read through both returned PMC body segments, including the continuation after character 16,000. Recent fastp publications were appraised from their abstracts and the official repository documentation, not independently benchmarked. ENA's download guidance was inspected for its checksum advice. No protected abstract is reproduced in this repository.

### Round 2 update — 2026-10-20

The narrow PubMed query `FASTQ[Title/Abstract] AND (checksum[Title/Abstract] OR "data integrity"[Title/Abstract])`, limited to publication dates 2022-01-01 through 2026-10-20, returned two records; both were screened. One data-article application was excluded and one compression paper retained for limited context. Its citation and abstract were retrieved directly. [search-update-02.json](search-update-02.json) preserves the exact query, IDs, decisions, and abstract-only limit; the original log is unchanged.

## What the sources support

| Source | Type and access | Relevant finding | Limit | Consequence here |
| --- | --- | --- | --- | --- |
| [Cock et al., 2010, PMID 20015970](https://pubmed.ncbi.nlm.nih.gov/20015970/) | Foundational format article; complete returned PMC body read | FASTQ variants can encode different quality scales and cannot always be distinguished from content alone. | A format description does not verify a given sample's origin. | Retain explicit `phred33` declaration; include it in the input lock without claiming it was inferred. |
| [Chen, 2023, PMID 38868435](https://pubmed.ncbi.nlm.nih.gov/38868435/) | Primary software paper; abstract-only appraisal | Describes a broader FASTQ preprocessing/QC tool and developments in duplication handling. | Author-reported performance was not reproduced; those functions are outside this implementation. | Keep the small parser's scope explicit; recommend established tools for broader preprocessing rather than inventing comparable capability. |
| [Chen, 2025, PMID 41112039](https://pubmed.ncbi.nlm.nih.gov/41112039/) | Primary software update; abstract-only appraisal | fastp 1.0 includes batch-processing and reporting-oriented development. | A later version's existence does not validate this tool or a file-identity lock. | Document an explicit handoff contract and failure behavior for this narrower workflow. |
| [ENA download documentation](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html) | Official resource; checksum guidance inspected 2026-10-20 | Recommends comparing download MD5 values with archive values to check transfer completeness. | Equality checks do not establish biological identity or suitability. | Keep upstream archive checks; add a local SHA-256 lock for exact files and sample sheet used downstream. |
| [fastp source, commit ee125a52fddae9d8189e13cd8a33ad04988a1351](https://github.com/OpenGene/fastp/tree/ee125a52fddae9d8189e13cd8a33ad04988a1351) | Official README and LICENSE inspected; v1.4.0 commit; MIT | Documents HTML/JSON reports and an option that refuses overwriting outputs. | No source execution or equivalent performance test was performed. | Use exclusive lock creation and clear machine-readable output; no code was copied. |

The local SHA-256 lock is an independent engineering choice. The cited sources motivate explicit contracts and integrity checks; none claims that this particular implementation establishes scientific validity.

### Round 2 update — 2026-10-20

| Source | Type/access | Actual support | Limit and implementation consequence |
| --- | --- | --- | --- |
| [Nazari et al., 2025, PMID 39747361](https://pubmed.ncbi.nlm.nih.gov/39747361/) | Primary compression study; citation and abstract only | Examines retention of different FASTQ components under compression. | Its compressor benchmarks were not reproduced and do not validate this lock. The project distinguishes exact raw-byte equality from parsed record meaning and tests recompression explicitly. |
| [ENA download guidance](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html), inspected 2026-10-20 | Official documentation | Recommends checksum comparison for transferred files. | Checksums do not authenticate biology. The optional QC flag checks the declared lock both before processing and against the bytes actually consumed. |

The integrated preflight is original code, not an implementation of GeneSqueeze or an ENA downloader.

## Changes made

Added `input_fingerprints.py`, six tests, and a lock for the existing public excerpt. The utility catches changed sample sheets, missing or changed files, and accidental lock overwrite. Tests explicitly show that gzip recompression changes a byte lock and that malformed content can still be fingerprinted: FASTQ validation remains a separate requirement. Existing QC calculations, paired-name rules, source data, and scientific reports are unchanged. The README now presents a consistent route to the [practical contract](practical-use.md).

### Round 2 update — 2026-10-20

Added optional `--input-lock` to `fastq_qc.py`, with six tests covering matched runs, earlier-report preservation, changed bytes after preflight, changed lock contents, output-path protection, and malformed-lock CLI failure. Unlocked runs keep the previous report structure. Locked runs add a small provenance object only after the consumed input bytes match.

## Remaining work

A future integrated preflight flag could close the operational gap between a separate verification command and QC. Broader schema validation and multi-platform testing would improve interoperability. Pair identity and contamination still need suitable additional evidence, not more checksum checks.

### Round 2 update — 2026-10-20

The integrated preflight proposed in round 1 is now implemented. A versioned output schema, paired-input lock convention, cross-platform checks, and stronger complete-directory publication remain open with acceptance criteria in [practical use](practical-use.md).

## Limits of this review

This was a single-reviewer, bounded PubMed and official-documentation review. It was not registered or duplicated and did not search every database or citation network. Four broad-search records remain unreturned; nonincluded records were screened at title level for direct relevance. Recent publications received abstract-level rather than full-method appraisal. Reported external software performance was not independently reproduced, and no comparative superiority claim is made.

### Round 2 update — 2026-10-20

The retained paper was appraised from its abstract; no compression algorithm was implemented or benchmarked. This update checks declared bytes without establishing their source authenticity, biological identity, or quality. It does not lock the filesystem, and final multi-file replacement is not an operating-system-wide transaction.

