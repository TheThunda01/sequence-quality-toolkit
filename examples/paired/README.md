# Synthetic paired FASTQ fixtures

These short records were written for testing and have no organism, accession, or biological origin. They are covered by the project's MIT license.

- `suffix_R1.fastq` and `suffix_R2.fastq`: two matching positions using `/1` and `/2` suffixes.
- `illumina_R1.fastq` and `illumina_R2.fastq`: two matching positions using synthetic seven-field Illumina-style identifiers and separate mate tokens.
- `mismatched_R2.fastq`: deliberately different first identifier; use with `suffix_R1.fastq` to trigger an error.

The sequences can have different lengths and are not designed as reverse complements. Pairing checks here use identifiers and record order, not sequence similarity. See [the rules and commands](../../docs/paired-fastq.md).
