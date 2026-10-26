# FASTQ methods and interpretation

FASTQ stores a sequence and one encoded quality score per position. The [glossary](glossary.md) and [assumptions](assumptions.md) explain the vocabulary and interpretation limits.

## File parsing and explicit encoding

The parser reads one record at a time and accepts wrapped sequence/quality lines. It checks the `@` header, `+` separator, optional repeated identifier, nonempty DNA sequence, and equal sequence/quality lengths. In a quality string, `@` and `+` are ordinary characters. Line breaks are removed; other whitespace in sequences or qualities is rejected. Read IDs are the first whitespace-delimited header token; descriptions are ignored. Duplicate read IDs are not checked in this streaming mode.

The manifest must declare `phred33`. Printable ASCII (a numeric character encoding) values 33–126 map to $`Q=0`$–$`93`$; this follows the Sanger FASTQ convention described by [Cock et al. (2010)](https://doi.org/10.1093/nar/gkp1137). This is a format bound, not a claim that a particular instrument produces every score. The overlapping character ranges of historical encodings make automatic detection unreliable. Declaring the wrong encoding can produce plausible but wrong summaries; the tool cannot rule that out.

The accepted DNA symbols and GC denominator match the [FASTA methods](methods.md). Gzip is detected from its magic bytes, not the filename. Python's gzip reader validates compressed streams when they are read to the end; truncated or corrupt inputs fail. A one-million-symbol per-read limit bounds malformed-record accumulation. This is an implementation limit, not a biological cutoff.

## Quality statistics

Q is a base-caller estimate on a logarithmic scale ([Illumina, n.d.](references.md#illumina-quality)): $`Q=-10\log_{10}(p)`$, so its implied error probability is $`p=10^{-Q/10}`$. Per-read expected errors sum those implied probabilities. Linearity of expectation permits this sum without assuming independent errors at different positions.

Expected errors are predictions, not counted or experimentally measured errors. Interpreting them requires calibrated scores: predicted probabilities must agree with observed error frequencies. Averaging Q and transforming it back to a probability also differs from averaging probabilities. The reports keep these calculations separate.

Per-read mean Q averages its base scores. The sample mean Q weights all bases equally, so longer reads contribute more. Q20 and Q30 fractions count bases meeting those score cutoffs. They are summaries, not universal acceptance rules. At cycle k, only reads with length at least k contribute; the output includes that denominator. No sequence position is padded with a score of zero.

Read-length histograms are exact. N counts are a subset of ambiguity counts. Quality values are summarized even at ambiguous bases because they are present in the file; they do not establish what the underlying base was.

## Streaming, fingerprints, and outputs

The program hashes raw source bytes as it reads them into the parser/decompressor. A gzip fingerprint therefore identifies the compressed file bytes; recompressing identical read content can change that fingerprint. The archive subset also has an uncompressed-content hash in its separate provenance record.

The program streams read-level JSON Lines to a temporary report directory. Memory grows with the longest read, distinct observed lengths, and per-cycle/per-sample summaries rather than with all read records. A million short reads still produce a large per-read output file; budget disk space accordingly.

The program validates every input before replacing the named report files with temporary outputs. A file-system error during replacement could leave a partial report set, so check the exit status.

The quality-summary command treats sample files independently. The separate [paired-file validator](paired-fastq.md) checks positional identifiers and mate labels; neither command establishes whether files are lanes from one library or samples are biological replicates. There is no reference genome and no alignment/mapping-quality calculation. Base-quality summaries do not establish identity, contamination, adapter content, duplication, or function.

## Relationship to established tools

| Tool | Published/documented scope | Relationship to this project |
| --- | --- | --- |
| [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/1%20Introduction/1.1%20What%20is%20FastQC.html) | A range of exploratory sequence-QC modules. | This project calculates a smaller set of transparent summaries; its report does not reproduce FastQC's modules or flags. |
| [fastp](https://doi.org/10.1093/bioinformatics/bty560) | FASTQ quality profiling and preprocessing, including filtering/trimming. | This project does not change reads or attempt fastp's preprocessing. |
| [MultiQC](https://doi.org/10.1093/bioinformatics/btw354) | Aggregates outputs from multiple analysis tools and samples. | This project writes its own reports; MultiQC integration is not implemented. |

No external-tool benchmark or equivalence check is claimed. FastQC, fastp, and MultiQC were not installed in the development runtime. The automated checks compare calculations with small known-answer examples and verify the included public-data fixture's recorded fingerprints.

See [related GitHub tools](related-tools.md) for the SeqKit and seqtk behavior inspected while designing paired-file validation.

## References

See the [complete bibliography](references.md) for Cock et al. (2010), Chen et al. (2018), Ewels et al. (2016), FastQC, ENA, and the quality-score definition, with DOIs, PMIDs, and access limits in the [reference audit](reference-audit.json).
