# Rapid literature and practice review

## Question and scope

Which small reliability improvement helps users carry an input identity from file receipt to a FASTQ QC run, while keeping byte integrity, format validation, and biological interpretation distinct? The review focused on file contracts and reporting. It did not compare aligners, establish assay-specific acceptance thresholds, or assess clinical use.

## Search record

Search date: **2026-10-20**. Exact queries, date restrictions, pagination limits, identifiers, and decisions are in [search-log.json](search-log.json). A recent broad PubMed query returned 14 records; the first 10, sorted by publication date, were screened. Four later records were not retrieved. A narrow `fastp[Title] OR fastplong[Title]` query returned two records, both inspected. The two pages contained 12 distinct records. A foundational known-title search returned zero; the known PMID was retrieved directly instead.

Two recent software papers were retained from the narrow search. The foundational FASTQ article was read through both returned PMC body segments, including the continuation after character 16,000. Recent fastp publications were appraised from their abstracts and the official repository documentation, not independently benchmarked. ENA's download guidance was inspected for its checksum advice. No protected abstract is reproduced in this repository.

## What the sources support

| Source | Type and access | Relevant finding | Limit | Consequence here |
| --- | --- | --- | --- | --- |
| [Cock et al., 2010, PMID 20015970](https://pubmed.ncbi.nlm.nih.gov/20015970/) | Foundational format article; complete returned PMC body read | FASTQ variants can encode different quality scales and cannot always be distinguished from content alone. | A format description does not verify a given sample's origin. | Retain explicit `phred33` declaration; include it in the input lock without claiming it was inferred. |
| [Chen, 2023, PMID 38868435](https://pubmed.ncbi.nlm.nih.gov/38868435/) | Primary software paper; abstract-only appraisal | Describes a broader FASTQ preprocessing/QC tool and developments in duplication handling. | Author-reported performance was not reproduced; those functions are outside this implementation. | Keep the small parser's scope explicit; recommend established tools for broader preprocessing rather than inventing comparable capability. |
| [Chen, 2025, PMID 41112039](https://pubmed.ncbi.nlm.nih.gov/41112039/) | Primary software update; abstract-only appraisal | fastp 1.0 includes batch-processing and reporting-oriented development. | A later version's existence does not validate this tool or a file-identity lock. | Document an explicit handoff contract and failure behavior for this narrower workflow. |
| [ENA download documentation](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html) | Official resource; checksum guidance inspected 2026-10-20 | Recommends comparing download MD5 values with archive values to check transfer completeness. | Equality checks do not establish biological identity or suitability. | Keep upstream archive checks; add a local SHA-256 lock for exact files and sample sheet used downstream. |
| [fastp source, commit ee125a52fddae9d8189e13cd8a33ad04988a1351](https://github.com/OpenGene/fastp/tree/ee125a52fddae9d8189e13cd8a33ad04988a1351) | Official README and LICENSE inspected; v1.4.0 commit; MIT | Documents HTML/JSON reports and an option that refuses overwriting outputs. | No source execution or equivalent performance test was performed. | Use exclusive lock creation and clear machine-readable output; no code was copied. |

The local SHA-256 lock is an independent engineering choice. The cited sources motivate explicit contracts and integrity checks; none claims that this particular implementation establishes scientific validity.

## Changes made

Added `input_fingerprints.py`, six tests, and a lock for the existing public excerpt. The utility catches changed sample sheets, missing or changed files, and accidental lock overwrite. Tests explicitly show that gzip recompression changes a byte lock and that malformed content can still be fingerprinted: FASTQ validation remains a separate requirement. Existing QC calculations, paired-name rules, source data, and scientific reports are unchanged. The README now presents a consistent route to the [practical contract](practical-use.md).

## Remaining work

A future integrated preflight flag could close the operational gap between a separate verification command and QC. Broader schema validation and multi-platform testing would improve interoperability. Pair identity and contamination still need suitable additional evidence, not more checksum checks.

## Limits of this review

This was a single-reviewer, bounded PubMed and official-documentation review. It was not registered or duplicated and did not search every database or citation network. Four broad-search records remain unreturned; nonincluded records were screened at title level for direct relevance. Recent publications received abstract-level rather than full-method appraisal. Reported external software performance was not independently reproduced, and no comparative superiority claim is made.
