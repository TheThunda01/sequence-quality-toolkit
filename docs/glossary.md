# Glossary

These terms explain the toolkit's reports and documentation. The two [data dictionaries](data-dictionary.md) and [FASTQ dictionary](fastq-data-dictionary.md) define individual output fields.

## Biology and sequence measurements

| Term | Meaning here |
| --- | --- |
| DNA and RNA | Deoxyribonucleic acid and ribonucleic acid, respectively: molecules that carry sequence information. DNA is commonly written with A, C, G, T; RNA uses U in place of T. |
| Base and nucleotide | A base is the letter-bearing part of a nucleotide. Here, “bases” in output names often means accepted sequence symbols, including ambiguity symbols. |
| A, C, G, T, U | Adenine, cytosine, guanine, thymine, and uracil. A DNA alphabet uses the first four. |
| Complement and reverse complement | DNA pairing maps A to T and C to G. A reverse complement also reverses the order, reflecting the opposite directions of paired strands. |
| Gene, transcript, transcription, and protein | A gene is a genomic feature; transcription produces RNA, including transcripts that may be translated into proteins. A read is not automatically a complete gene or transcript. |
| cDNA and RNA-seq | Complementary DNA is made from RNA. Many RNA-sequencing workflows sequence cDNA, explaining why RNA-derived reads use DNA letters. |
| Library, fragment, read, and base call | A library is prepared material for sequencing; a fragment is a piece of that material; a read is its reported sequence; a base call is the assigned symbol at one position. |
| Paired-end, mate, R1, and R2 | Sequencing both ends of one fragment yields two associated reads, called mates or R1/R2. They need not overlap or be exact reverse complements. |
| Single-end | Sequencing one end of each measured fragment. The bundled public yeast excerpt has this layout. |
| Biological replicate and technical run | A biological replicate samples a separate biological unit; a technical run measures prepared material. Neither two mates nor two files alone establish biological independence. |
| Wild type | The archive's label for the study's reference condition; it does not mean this toolkit verified a genotype or identified the organism. |
| IUPAC ambiguity codes | Standard letters specifying alternative bases. R means A/G, Y C/T, S C/G, W A/T, K G/T, M A/C, B C/G/T, D A/G/T, H A/C/T, V A/C/G, and N any DNA base. IUPAC names the International Union of Pure and Applied Chemistry. |
| Canonical bases and GC fraction | Canonical here means A/C/G/T. GC fraction is $`\frac{G+C}{A+C+G+T}`$; all ambiguity symbols are excluded from its denominator. |
| Assembly, contig, and N50 | An assembly reconstructs longer sequences; a contig is a contiguous assembled sequence. N50 is the length reached when longest-first records account for at least half of total length. Arbitrary-string N50 does not validate an assembly. |
| Alignment, mapping quality, and variant | Alignment places a read against a reference. Mapping quality concerns confidence in that placement. A variant is a sequence difference relative to a reference. None is inferred here. |
| Adapter, trimming, and contamination | An adapter is a technical sequence used in library preparation; trimming removes sequence portions; contamination is unintended material. This toolkit does not detect adapters, trim, or establish contamination status. |

## Quality and statistics

| Term | Meaning here |
| --- | --- |
| Phred score (Q) | A logarithmic estimate of base-call error: $`Q=-10\log_{10}(p)`$, where $`p`$ is the estimated error probability. Higher scores imply smaller predicted error probabilities. |
| Phred+33 | Encoding a Q score as a text character whose ASCII numeric value is `Q+33`. A declared encoding is required; overlapping historical ranges prevent certain inference from characters alone. |
| Q20 and Q30 fraction | Fraction of accepted symbols with scores at least 20 or 30. They are descriptive thresholds, not automatic pass/fail standards. |
| Calibration and observed error | Calibration is agreement between predicted probabilities and observed frequencies. This toolkit has no truth reference for observing errors or checking calibration. |
| Expected errors | Sum of quality-implied error probabilities across positions. This estimates an expected count if those probabilities are appropriate; it does not count actual mistakes. Linearity of expectation does not require independent positions. |
| Base-weighted mean and per-read mean | The first gives every position equal weight across a file; the second averages within a read. Longer reads contribute more to the base-weighted mean. |
| Cycle and denominator | A cycle is a one-based position in a read. Its denominator counts only reads that reach that position. The software does not invent missing late positions. |
| Histogram | Counts for each observed value, such as exact read length or integer Q score. |
| Convenience prefix | The first records in file order, selected for a manageable example. It is not a random or representative sample of the full run. |

## Files and software

| Term | Meaning here |
| --- | --- |
| FASTA and FASTQ | Text formats containing identifiers and sequences; FASTQ also includes a quality character per sequence position. Wrapped records span multiple lines. |
| Header, identifier, and manifest | A header introduces a record; its first token is this parser's identifier. A manifest is a table declaring which files or records belong to which user labels. |
| Gzip and magic bytes | Gzip compresses file content; characteristic initial bytes identify that format even when a filename has no `.gz` suffix. |
| ASCII, UTF-8, and whitespace | Character encodings and separators such as spaces or tabs. FASTQ quality decoding here uses printable ASCII values 33–126. |
| CSV, JSON, and JSON Lines (JSONL) | Comma-separated tables, structured text objects, and one JSON object per line. `null` denotes an undefined value rather than zero. A schema specifies field names and types. |
| Streaming and snapshot | Streaming processes records incrementally; a snapshot holds selected bytes together. FASTQ is streamed, while this small FASTA workflow stores its input in memory. |
| Checksum, SHA-256, MD5, and fingerprint | Algorithms and identifiers calculated from bytes. SHA-256 pins local files; the historic ENA download check uses the archive's MD5. Equality does not authenticate the source or prove biological accuracy. |
| Input lock and provenance | A lock records expected file identities; provenance records where files, labels, and settings came from. Recompressing identical reads can change a byte lock. |
| Preflight, staged output, and transaction | Preflight checks inputs before processing; staging writes temporary output before replacement. A transaction would make a whole group of replacements indivisible; this toolkit does not promise that. |
| CLI, exit status, and CI | Command-line interface, integer completion code, and continuous integration. Check exit status; a CI configuration file alone does not show that a hosted run passed. |
| ENA, SRA, INSDC, and accession | European Nucleotide Archive, Sequence Read Archive, International Nucleotide Sequence Database Collaboration, and a persistent archive identifier. The run is `ERR458493`; its project is `PRJEB5348`. |
| API and commit | An application programming interface is a defined software interface; a Git commit identifies a repository revision. |
| AI | Artificial intelligence, used here only to disclose assistance with implementation and documentation. It does not describe a biological prediction model in this toolkit. |
| UMI | Unique molecular identifier, a tag used in some protocols to track molecules. Extra UMI header fields are outside this paired-header grammar. |
| MIT | The project code's software-license name. Public archive data retain their separate attribution and access terms. |

