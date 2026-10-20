# Biology and concepts behind the checks

## What a sequencing read represents

A read is a sequence reported by a sequencing instrument and its analysis software. In the short-read example here, it covers part of a library molecule, rather than a complete chromosome or gene. DNA sequencing and RNA sequencing therefore produce collections of observations that need additional analysis before they can answer biological questions.

In many RNA-seq workflows, RNA is represented by complementary DNA, or cDNA, before sequencing. That is why a file from an RNA experiment can use the DNA alphabet, including T, rather than U. Early yeast RNA-seq work illustrates this connection between cDNA reads and transcript measurements ([Nagalakshmi et al., 2008](https://doi.org/10.1126/science.1158441)). A read count is not automatically a molecule count: how the library was prepared, which fragments were sequenced, and how reads are assigned all matter.

## Bases, ambiguity, and complementarity

DNA is commonly represented with A, C, G, and T. In ordinary complementary DNA pairing, A pairs with T and C with G; RNA uses U in place of T. The two DNA strands run in opposite directions, so a reverse complement changes both the base letters and their order ([NCBI: DNA structure](https://www.ncbi.nlm.nih.gov/books/NBK26821/); [RNA structure](https://www.ncbi.nlm.nih.gov/books/NBK26887/)).

Some sequence positions use ambiguity codes. For example, R allows A or G, while N allows any of the four DNA bases. These symbols describe uncertainty or alternatives at a position; they are not extra DNA bases ([NCBI nucleotide codes](https://www.ncbi.nlm.nih.gov/books/NBK44863/table/sequencesquickstart.Td/?report=objectonly)). An N count can reveal how often the file leaves a base unspecified, but it does not explain why.

This toolkit calculates GC using only A, C, G, and T in the denominator. Ambiguous positions are excluded, even when an ambiguity code constrains the possibilities. That explicit convention makes comparisons interpretable; it does not make GC a test of sample identity or purity.

## FASTA, FASTQ, and estimated quality

FASTA associates a sequence with a header. FASTQ also provides a quality score for each sequence position. Matching sequence and quality lengths is therefore a meaningful structural check: without that match, scores cannot be assigned unambiguously to positions.

Phred quality expresses an estimated base-call error probability: Q = −10 log10(p). Q20 corresponds to p=0.01 and Q30 to p=0.001 under that model. Those are predictions, not observed error frequencies. Calibration can differ across data, and a high score does not establish that a read maps uniquely or comes from the expected organism. Historical FASTQ encodings also differ, which is why the workflow requires an explicit Phred+33 declaration ([Cock et al., 2010](https://doi.org/10.1093/nar/gkp1137)).

The mean of quality scores and the mean of their implied error probabilities answer different questions because the transformation is nonlinear. The reports keep score summaries separate from expected-error calculations rather than treating them as interchangeable evidence.

## Why per-cycle denominators matter

A cycle summary groups positions by their order within each read. If one read is 50 bases long and another is 75, both contribute to cycle 40, but only the longer read contributes to cycle 60. Filling the missing position with zero would invent an observation and lower the mean incorrectly.

The toolkit therefore reports how many reads reach each position. Changes near the end of a plot can reflect both a change in quality and a change in which reads remain represented. These summaries describe the supplied files; they do not identify the cause of a pattern.

## Read pairs are not transcripts

Paired-end sequencing reads both ends of a library fragment ([Illumina's explanation](https://www.illumina.com/science/technology/next-generation-sequencing/plan-experiments/paired-end-vs-single-read.html)). R1 and R2 are associated observations, not two independent biological replicates. They are also not necessarily identical or exact reverse complements: their sequenced portions may not overlap.

A pairing check asks whether corresponding records use matching supported identifiers, the expected mate labels, and consistent ordering. It does not establish the fragment's genomic location. In RNA-seq, a fragment may represent part of a transcript; a read pair is not automatically a complete transcript, a unique gene assignment, or a count of one original RNA molecule.

The [paired-file guide](paired-fastq.md) states exactly which header conventions this project accepts.

## N50 describes lengths, not correctness

N50 is the sequence length at which records ordered from longest to shortest account for at least half the total length. For lengths 10, 6, and 4, the total is 20 and N50 is 10. [NCBI's assembly reference](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/) defines this convention for assembly statistics.

The same arithmetic can be applied to arbitrary strings, but its interpretation depends on what those strings represent. A larger N50 cannot by itself show that an assembly is correct, complete, or free from contamination. Pooling unrelated samples also changes the question, so this project distinguishes pooled and per-sample summaries.

## What the yeast example can support

The included public example is a prefix of 1,000 reads from **ERR458493**, a single-end yeast RNA-seq run in **PRJEB5348** ([official run record](https://www.ncbi.nlm.nih.gov/sra/ERR458493)). It has no bundled R2 counterpart. The underlying study investigated RNA-seq analysis using extensive replication ([Schurch et al., 2016](https://doi.org/10.1261/rna.053959.115)); this repository does not reproduce that experiment's analysis.

The prefix tests the software on real archived data. It is not a random or representative sample of the full run. Synthetic fixtures separately exercise known failure cases. Passing these checks supports a claim about file consistency and implemented calculations, not differential expression, mechanism, organism identity, or experimental success.

## Further reading

- [Public-data provenance](public-data.md): source verification, selection, and reuse terms.
- [FASTQ methods](fastq-methods.md): exact calculations and implementation boundaries.
- [Cock et al.](https://doi.org/10.1093/nar/gkp1137): FASTQ conventions and quality encodings.
- [Schurch et al.](https://doi.org/10.1261/rna.053959.115): the source study and its biological-replication context.
