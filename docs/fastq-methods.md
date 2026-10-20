# FASTQ methods and interpretation

## File parsing and explicit encoding

The parser reads one record at a time and accepts wrapped sequence/quality lines. It checks the `@` header, `+` separator, optional repeated identifier, nonempty DNA sequence, and equal sequence/quality lengths. In a quality string, `@` and `+` are ordinary characters. Line breaks are removed; other whitespace in sequences or qualities is rejected. Read IDs are the first whitespace-delimited header token; descriptions are ignored. Duplicate read IDs are not checked in this streaming mode.

The manifest must declare `phred33`. Printable ASCII 33–126 maps to Q=0–93; this follows the Sanger FASTQ convention described by [Cock et al. (2010)](https://doi.org/10.1093/nar/gkp1137). This is a format bound, not a claim that a particular instrument produces every score. The overlapping character ranges of historical encodings make automatic detection unreliable. Declaring the wrong encoding can produce plausible but wrong summaries; the tool cannot rule that out.

The accepted DNA symbols and GC denominator match the [FASTA methods](methods.md). Gzip is detected from its magic bytes, not the filename. Python's gzip reader validates compressed streams when they are read to the end; truncated or corrupt inputs fail. A one-million-symbol per-read limit bounds malformed-record accumulation. This is an implementation limit, not a biological cutoff.

## Quality statistics

Q is a base-caller estimate on a logarithmic scale: Q = −10 log10(p), so its implied error probability is p = 10^(−Q/10). Per-read expected errors sum those implied probabilities. The result depends on score calibration and is not a counted or experimentally measured error rate. Averaging Q and transforming it back to a probability is not the same as averaging probabilities; both are kept conceptually separate here.

Per-read mean Q averages its base scores. The sample mean Q weights all bases equally, so longer reads contribute more. Q20 and Q30 fractions count bases meeting those score cutoffs. They are summaries, not universal acceptance rules. At cycle k, only reads with length at least k contribute; the output includes that denominator. No sequence position is padded with a score of zero.

Read-length histograms are exact. N counts are a subset of ambiguity counts. Quality values are summarized even at ambiguous bases because they are present in the file; they do not establish what the underlying base was.

## Streaming, fingerprints, and outputs

Raw source bytes are hashed while they pass into the parser/decompressor. A gzip fingerprint therefore identifies the compressed file bytes; recompressing identical read content can change that fingerprint. The archive subset also has an uncompressed-content hash in its separate provenance record.

Read-level JSON Lines are streamed to a temporary report directory. Memory grows with the longest read, distinct observed lengths, and per-cycle/per-sample summaries rather than with all read records. A million short reads still produce a large per-read output file; budget disk space accordingly. Full input validation completes before temporary outputs replace the named report files. A later file-system error during replacement could leave a partial report set; check the exit status.

Sample files are independent. This version cannot establish whether mates have corresponding identifiers, whether two files are lanes from one library, or whether samples are biological replicates. It has no reference genome and does not calculate alignment/mapping quality. Base-quality summaries do not establish identity, contamination, adapter content, duplication, or function.

## Relationship to established tools

| Tool | Published/documented scope | Relationship to this project |
| --- | --- | --- |
| [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/1%20Introduction/1.1%20What%20is%20FastQC.html) | A range of exploratory sequence-QC modules. | This project calculates a smaller set of transparent summaries; its report does not reproduce FastQC's modules or flags. |
| [fastp](https://doi.org/10.1093/bioinformatics/bty560) | FASTQ quality profiling and preprocessing, including filtering/trimming. | This project does not change reads or attempt fastp's preprocessing. |
| [MultiQC](https://doi.org/10.1093/bioinformatics/btw354) | Aggregates outputs from multiple analysis tools and samples. | This project writes its own reports; MultiQC integration is not implemented. |

No external-tool benchmark or equivalence check is claimed. FastQC, fastp, and MultiQC were not installed in the development runtime. The automated checks compare calculations with small known-answer examples and verify the included public-data fixture's recorded fingerprints.

## References

- Cock PJA, Fields CJ, Goto N, Heuer ML, Rice PM. (2010). The Sanger FASTQ file format for sequences with quality scores, and the Solexa/Illumina FASTQ variants. *Nucleic Acids Research*, 38(6), 1767–1771. https://doi.org/10.1093/nar/gkp1137.
- Andrews S. FastQC documentation. Babraham Bioinformatics. https://www.bioinformatics.babraham.ac.uk/projects/fastqc/. Accessed 20 October 2026.
- Chen S, Zhou Y, Chen Y, Gu J. (2018). fastp: an ultra-fast all-in-one FASTQ preprocessor. *Bioinformatics*, 34(17), i884–i890. https://doi.org/10.1093/bioinformatics/bty560.
- Ewels P, Magnusson M, Lundin S, Käller M. (2016). MultiQC: summarize analysis results for multiple tools and samples in a single report. *Bioinformatics*, 32(19), 3047–3048. https://doi.org/10.1093/bioinformatics/btw354.
- ENA. Archive-generated files. https://ena-docs.readthedocs.io/en/latest/retrieval/file-download/archive-generated-files.html. Accessed 20 October 2026. Defines the archive's Phred+33 output convention used for this public example.
