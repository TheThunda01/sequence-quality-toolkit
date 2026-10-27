# Project context

FASTA stores a sequence and header; FASTQ adds a quality value at each sequence position. Quality control (QC) here means checking these files and summarizing their declared measurements.

## Where this fits

[Pasilla expression QC](https://github.com/TheThunda01/pasilla-expression-qc) continues the measurement-quality theme with count tables, sample labels, and normalization. Read it after this toolkit to see how checks change with the type of measurement. Its fruit-fly counts are separate from this toolkit’s yeast-read example; the projects do not form one sequencing pipeline. Return to the [portfolio guide](https://github.com/TheThunda01/TheThunda01/blob/main/PROJECT_GUIDE.md).

## Background and rationale

Check the files before interpreting sequencing data. Records must be readable, sample labels must match the data, and quality summaries need clear definitions. FASTQ stores both sequence and estimated base-call quality. Its historical encoding variants make the choice of quality encoding important ([Cock et al., 2010](https://doi.org/10.1093/nar/gkp1137)).

This project explains a small set of reproducible checks: how each calculation works, which information it uses, and what its result can support.

## What it does

The FASTA workflow checks identifiers and sample mappings, then reports lengths, ambiguity counts, GC fractions, and length N50. The FASTQ workflow reads plain or compressed files, requires an explicit quality encoding, and reports quality and length summaries for each file, read, and sequence position. Input fingerprints connect the results to the exact files used.

A separate paired-file check validates matching identifiers and mate labels in record order, without changing reads.

The examples combine deliberately imperfect synthetic data with a small excerpt from a public yeast RNA-seq experiment. Tests cover malformed records, undefined fractions, inconsistent metadata, and reproducible output.

## Why it matters

These checks can catch file and metadata problems before a larger analysis makes them harder to trace. Explicit denominators also prevent misleading comparisons. A mean across bases differs from a mean across reads, and a position summary should include only reads that reach that position.

Established tools such as [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/) address a broader range of QC questions. This toolkit is a focused, inspectable learning project, not a replacement for a complete sequencing workflow.

## Key themes

- **Data integrity:** validate records and sample mappings before summarizing them.
- **Reproducibility:** keep inputs, definitions, fingerprints, and outputs connected.
- **Scientific interpretation:** separate descriptive metrics from biological conclusions.
- **Software practice:** stream read data, test edge cases, and explain failures.

## How to read the public example

The [glossary](glossary.md) defines the terms, and [assumptions](assumptions.md) states what is checked and what remains untested. N50 describes a length distribution; GC describes a declared fraction of sequence symbols. Neither identifies an organism or validates an assembly.

The real-data example contains the first 1,000 reads from [ERR458493](https://www.ncbi.nlm.nih.gov/sra/ERR458493), linked to [Schurch et al. (2016)](https://doi.org/10.1261/rna.053959.115). It is a convenience prefix, not a representative sample. Its results describe that excerpt only; they do not assess the whole run, reproduce the study, verify organism identity, or establish a biological effect. Quality scores are estimates, not observed error counts.
