# Paired FASTQ consistency checks

FASTQ stores a read and an encoded quality score for each position. R1 and R2 denote the two read files expected from paired-end sequencing. `paired_fastq_check.py` checks two files together, one record from each file at a time. It requires valid FASTQ, equal nonzero read counts, matching normalized identifiers at each position, and a mate-1 label in R1 with a mate-2 label in R2. Plain text, gzip, and a mixture of the two are accepted. Quality encoding must be explicitly declared `phred33`.

The command stops at the first problem and exits with status 2. It does not repair, reorder, trim, or filter reads. Input file names do not determine pairing; the record headers do.

## Run the synthetic examples

Suffix convention:

```sh
python paired_fastq_check.py --read1 examples/paired/suffix_R1.fastq --read2 examples/paired/suffix_R2.fastq --name-convention suffix --quality-encoding phred33 --sample-id synthetic_suffix --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir reports/paired_suffix
```

Illumina convention:

```sh
python paired_fastq_check.py --read1 examples/paired/illumina_R1.fastq --read2 examples/paired/illumina_R2.fastq --name-convention illumina --quality-encoding phred33 --sample-id synthetic_illumina --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir reports/paired_illumina
```

Each example has two paired records. The sequences were written for testing and deliberately need not have equal lengths or be reverse complements. The public yeast example elsewhere in this repository is **single-end** and is not used to demonstrate paired-end validation.

## Supported identifiers

Choose a convention explicitly; the program does not infer one or mix conventions within a run.

| Convention | Accepted example | Normalized comparison key |
| --- | --- | --- |
| `suffix` | `@fragment_001/1` and `@fragment_001/2` | `fragment_001` |
| `illumina` | `@MACHINE:1:FLOW:1:1101:100:200 1:N:0:ACGT` and the corresponding `2:N:0:ACGT` | `MACHINE:1:FLOW:1:1101:100:200` |

In `suffix` mode, the first token must end in `/1` or `/2`. The key starts with a letter/digit and otherwise allows letters, digits, `.`, `_`, `:`, `#`, or `-`. A nested suffix such as `fragment/1/2` is rejected. Descriptions are ignored, except additional recognized mate annotations are rejected as ambiguous.

In `illumina` mode, exactly two whitespace-separated tokens are required. The first has seven colon-separated fields: instrument, run, flowcell, lane, tile, x, and y. Run/lane/tile are integers; x/y may be signed integers. Instrument/flowcell allow letters, digits, `.`, `_`, and `-`. The second token has mate `1` or `2`, filter flag `Y` or `N`, an integer control field, and a nonempty sample/index field using letters, digits, `+`, `.`, or `-`. Additional unique molecular identifier (UMI) fields or other header layouts are not supported. These are this project's explicit input rules, informed by the [documented Illumina layout](https://help.connected.illumina.com/basespace/files-used-by-basespace/fastq-files), not a claim to exactly reproduce its character restrictions or accept every historical variant. The vendor page uses narrower instrument/flowcell character sets and a numeric sample field; this project deliberately accepts the characters stated above. The key comparison also does not establish that a sample/index tag identifies the same biological specimen.

Comparison keys are case-sensitive. Filter/control/sample-index fields are parsed but not compared across mates. Unlabeled archive identifiers, missing mate labels, wrong-direction labels, and mixed conventions fail rather than being silently matched.

## Interpret the report

Success writes `report.json` and `report.md`, including read counts, selected rules, and SHA-256 hashes of the raw input bytes. Validation finishes before reports are replaced. Failed validation leaves an existing report unchanged; always check the exit status. File-system errors during replacement can still leave a partial report set.

This is **positional consistency**, not proof that fragments are biologically paired. Repeated keys at different positions are not checked for uniqueness. No sequence content, strand orientation, overlap, transcript assignment, or genomic location is inferred. See [biology and concepts](biology-and-concepts.md) and [related tools](related-tools.md) for context.
