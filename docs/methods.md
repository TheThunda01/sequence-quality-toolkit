# FASTA methods, choices, and limits

This page describes `sequence_qc.py`. The separate [FASTQ methods](fastq-methods.md) cover the streaming read-quality workflow added in version 0.2.0.

## Scope

The FASTA workflow answers a file-level question: are the records and their manifest internally consistent, and what are their lengths and symbol counts? FASTA stores identifiers and sequences; a manifest assigns those identifiers to user-supplied sample labels. It does not perform read alignment, taxonomic classification, sequence assembly, variant calling, functional annotation, or reference comparison.

## Symbols and GC

The accepted DNA alphabet follows the standard unambiguous bases and ambiguity codes shown in [NCBI's nucleotide-code reference](https://www.ncbi.nlm.nih.gov/sites/books/NBK44863/table/sequencesquickstart.Td/?report=objectonly). Ambiguity symbols describe allowed alternatives; this tool counts them but does not guess their underlying bases. The parser's restricted ID characters, rejection of gaps and `U`, and two-column manifest are project design decisions, not universal requirements of all FASTA readers.

The GC fraction is defined here as `(G + C) / (A + C + G + T)`. All ambiguity symbols are excluded from that denominator, including S and W. This is an explicit convention, not a claim that it is the only possible GC definition. A sequence with no unambiguous bases has undefined GC. The aggregate GC value is calculated from all pooled symbols; averaging sequence percentages would give each short and long sequence equal influence, which is a different statistic.

## Length N50

[NCBI's genome assembly report reference](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/) defines the N50 length by cumulative sequence coverage. The implementation sorts positive lengths from largest to smallest and returns the length where cumulative length first reaches at least half the total. An exact half-total boundary therefore qualifies. Integer arithmetic avoids floating-point comparisons at that boundary.

The formula does not require an assembly. Its interpretation does. These arbitrary strings and mixed sample labels are not assembled contigs, so their pooled N50 is simply a worked arithmetic example. Even for an actual assembly, contiguity alone cannot demonstrate correctness or completeness. This tool does not validate either property.

Version 0.2.0 also calculates N50 and GC separately for each manifest sample label. This avoids pooling labels in the sample report, but the labels alone still do not establish that records constitute an assembly.

## Reproducibility and failure behavior

The report includes SHA-256 input-file fingerprints and a tool version. The CLI validates both inputs before writing output. Invalid records, duplicate identifiers, missing mappings, extra mappings, and unsupported symbols stop the run with exit status 2. This avoids silently dropping mismatches. File-system write failures can still leave partial outputs; check exit status and rerun into a writable directory.

The FASTA implementation snapshots each file's bytes, then parses and fingerprints that snapshot. It keeps both input bytes and records in memory and is intended for small teaching fixtures. This command is not a large-genome streaming tool and does not read compressed FASTA. Use `fastq_qc.py` for streaming plain/gzip FASTQ quality summaries.

## Sources

[NCBI's nucleotide-code table](references.md#ncbi-codes) supports the DNA-symbol vocabulary; [NCBI's assembly report](references.md#ncbi-assembly) supports the N50 convention. Complete metadata and current access levels are in [References](references.md) and the [reference audit](reference-audit.json). Fixture counts come from executing this repository, not those sources.
