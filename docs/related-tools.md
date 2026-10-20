# Related tools and design choices

Established repositories helped define useful questions for this project. The implementation here was written separately; no source code was copied, and no performance or output equivalence is claimed.

| Repository inspected | Relevant documented behavior | How this project differs |
| --- | --- | --- |
| [SeqKit](https://github.com/shenwei356/seqkit), especially [`pair.go`](https://github.com/shenwei356/seqkit/blob/c784d97c7e7d941c7fc3f00694044b6844affb4b/seqkit/cmd/pair.go) and the [pair guide](https://bioinf.shenwei.me/seqkit/usage/#pair) | Matches records from two FASTQ files, can write unpaired records, and supports a configurable identifier expression for suffix conventions. Its guide discusses buffering when records are out of order. | This validator stops at the first positional mismatch. It writes a consistency report, does not create repaired FASTQs, and supports only two explicitly chosen name grammars. |
| [seqtk](https://github.com/lh3/seqtk), especially its [README](https://github.com/lh3/seqtk/blob/94e707082d39b0a038f234df676e32d9802c0dc7/README.md) | Provides FASTA/FASTQ transformations and gzip input. The README demonstrates subsampling mate files with the same random seed. | This project performs neither transformation nor subsampling during validation. It checks the supplied files without altering them. |

Sources were inspected on 20 October 2026 at the linked revisions. The useful design lessons were to make the identifier rule explicit, preserve raw inputs, and distinguish checking consistency from changing a dataset. Those are design choices, not evidence that this small implementation has the same coverage as the established tools.

For broader quality summaries, see the [FastQC, fastp, and MultiQC comparison](fastq-methods.md#relationship-to-established-tools). The upstream tools were not installed or benchmarked in this development runtime. Their repository descriptions and documented behavior inform this comparison; the project's tests validate its own specified rules.
