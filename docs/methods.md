# Methods, choices, and limits

## Scope

This project answers a file-level question: are the records and their manifest internally consistent, and what are their lengths and symbol counts? It does not perform read alignment, taxonomic classification, sequence assembly, variant calling, functional annotation, or reference comparison.

## Symbols and GC

The accepted DNA alphabet follows the standard unambiguous bases and ambiguity codes shown in [NCBI's nucleotide-code reference](https://www.ncbi.nlm.nih.gov/sites/books/NBK44863/table/sequencesquickstart.Td/?report=objectonly). Ambiguity symbols describe allowed alternatives; this tool counts them but does not guess their underlying bases. The parser's restricted ID characters, rejection of gaps and `U`, and two-column manifest are project design decisions, not universal requirements of all FASTA readers.

GC is defined here as `(G + C) / (A + C + G + T)`. All ambiguity symbols are excluded from that denominator, including S and W. This is an explicit convention, not a claim that it is the only possible GC definition. A sequence with no unambiguous bases has undefined GC. The aggregate GC value is calculated from all pooled symbols; averaging sequence percentages would give each short and long sequence equal influence, which is a different statistic.

## Length N50

[NCBI's genome assembly report reference](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/) defines the N50 length by cumulative sequence coverage. The implementation sorts positive lengths from largest to smallest and returns the length where cumulative length first reaches at least half the total. An exact half-total boundary therefore qualifies. Integer arithmetic avoids floating-point comparisons at that boundary.

The formula does not require an assembly. Its interpretation does. These arbitrary strings and mixed sample labels are not assembled contigs, so their pooled N50 is simply a worked arithmetic example. Even for an actual assembly, contiguity alone cannot demonstrate correctness or completeness. This tool does not validate either property.

## Reproducibility and failure behavior

The report includes SHA-256 input-file fingerprints and a tool version. The CLI validates both inputs before writing output. Invalid records, duplicate identifiers, missing mappings, extra mappings, and unsupported symbols stop the run with exit status 2. This avoids silently dropping mismatches. File-system write failures can still leave partial outputs; check exit status and rerun into a writable directory.

The implementation snapshots each file's bytes, then parses and fingerprints that snapshot. It keeps both the input bytes and records in memory and is intended for small teaching fixtures. It is not a large-genome streaming tool. It does not support FASTQ quality scores, compressed inputs, or a directory of samples.

## Sources

1. National Center for Biotechnology Information. *Entrez Sequences Help: nucleotide codes*. https://www.ncbi.nlm.nih.gov/sites/books/NBK44863/table/sequencesquickstart.Td/?report=objectonly. Accessed 20 October 2026. Used for the accepted DNA-symbol vocabulary.
2. National Center for Biotechnology Information. *NCBI Datasets: genome assembly report*. https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/. Accessed 20 October 2026. Used for the N50 length convention only; the project does not reproduce an NCBI assembly analysis.

The fixture counts and reported values come from executing this repository, not from these sources. No empirical biological conclusion is drawn from them.
