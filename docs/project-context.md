# Project context

## Background and rationale

Before asking a biological question with sequencing data, it helps to understand the files themselves. Are the records readable? Do sample labels match the data? What do the read lengths and quality scores look like? FASTQ stores both sequence and estimated base-call quality, and its historical encoding variants make assumptions about those scores important ([Cock et al., 2010](https://doi.org/10.1093/nar/gkp1137)).

This project makes a small set of those checks visible and reproducible. The aim is to show how a QC calculation works, what information it uses, and where its interpretation stops.

## What it does

The FASTA workflow checks identifiers and sample mappings, then reports lengths, ambiguity counts, GC fractions, and length N50. The FASTQ workflow reads plain or compressed files, requires an explicit quality encoding, and reports quality and length summaries for each file, read, and sequence position. Input fingerprints connect the results to the exact files used.

A separate paired-file check validates matching identifiers and mate labels in record order, without changing reads.

The examples combine deliberately imperfect synthetic data with a small excerpt from a public yeast RNA-seq experiment. Tests cover malformed records, undefined fractions, inconsistent metadata, and reproducible output.

## Why it matters

These checks can surface file and metadata problems before they become harder to trace in a larger analysis. Clear denominators also prevent misleading comparisons: a mean across bases differs from a mean across reads, and a sequence position should only include reads that reach it.

Established tools such as [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/) address a broader range of QC questions. This toolkit is a focused, inspectable learning project, not a replacement for a complete sequencing workflow.

## Key themes

- **Data integrity:** validate records and sample mappings before summarizing them.
- **Reproducibility:** keep inputs, definitions, fingerprints, and outputs connected.
- **Scientific interpretation:** separate descriptive metrics from biological conclusions.
- **Software practice:** stream read data, test edge cases, and explain failures.

## How to read the public example

The real-data example contains the first 1,000 reads from [ERR458493](https://www.ncbi.nlm.nih.gov/sra/ERR458493), linked to [Schurch et al. (2016)](https://doi.org/10.1261/rna.053959.115). It is a convenience prefix, not a representative sample. Its results describe that excerpt only; they do not assess the whole run, reproduce the study, verify organism identity, or establish a biological effect. Quality scores are estimates, not observed error counts.
