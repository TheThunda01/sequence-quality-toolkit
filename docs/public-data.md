# Public yeast example: source and limits

## What is included

`examples/public/ERR458493_first1000.fastq.gz` contains the first 1,000 archived records from **ERR458493**, an Illumina HiSeq 2000 single-end RNA-seq run submitted by Dundee. The official record labels the organism *Saccharomyces cerevisiae*, the library `wild type`, and the project **PRJEB5348**. See the [NCBI run record](https://www.ncbi.nlm.nih.gov/sra/ERR458493) and [ENA project](https://www.ebi.ac.uk/ena/browser/view/PRJEB5348).

This is a convenience prefix, not random sampling. Read order can correlate with technical features. Its summaries are useful for checking code on real archived reads, not for judging the entire run or comparing conditions. Organism and library labels come from the archive; the project does not independently verify them.

The underlying experiment is described in Schurch et al. (2016), [*How many biological replicates are needed in an RNA-seq experiment and which differential expression tool should you use?*](https://doi.org/10.1261/rna.053959.115), *RNA*, 22(6), 839–851. The associated [erratum](https://doi.org/10.1261/rna.058339.116) is also available. This repository uses a tiny read excerpt for QC and does not reproduce the paper's expression analysis or its conclusions.

## How the excerpt was made

On 20 October 2026, the [ENA file report](https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERR458493&result=read_run&fields=run_accession,scientific_name,library_layout,fastq_ftp,fastq_md5,fastq_bytes&format=tsv) supplied the source URL, compressed size, and MD5:

| Property | Recorded value |
| --- | --- |
| Complete compressed bytes | 59,532,325 |
| Complete-file MD5 | `2b8c708cce1fd88e7ddecd51e5ae2154` |
| Source | `https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR458/ERR458493/ERR458493.fastq.gz` |
| Selected records | First 1,000 in archive order |
| Subset gzip bytes | 51,967 |
| Subset gzip SHA-256 | `4e380e55e0dfa36b1439c57138e123c59af4da2a289a0d2adfca085c2d6e76b4` |

The complete download matched the archive's size and MD5. Original record bytes were preserved in the selected prefix and compressed with a fixed timestamp and no embedded filename. The JSON [provenance record](../examples/public/provenance.json) additionally stores the uncompressed-content SHA-256 and first/last identifiers. This identifies exactly what was used; a checksum does not validate biology.

The Phred+33 declaration follows the documented [ENA archive-generated FASTQ format](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download/archive-generated-files.html), not a guess from the characters.

## Rebuild or use the full run

```sh
python scripts/fetch_public_example.py
make demo
```

The optional retrieval script downloads the complete ~60 MB archive into a temporary directory, verifies its recorded size and MD5, then recreates the subset and provenance. It does not silently accept a changed source. You can reuse a complete downloaded file with `--source-file /path/to/ERR458493.fastq.gz`. The default QC command never downloads anything.

For a full-run analysis, download the archive from the source above, verify the recorded MD5, and create your own manifest pointing to that complete file. Use a new output directory and a label that identifies the full run. Expect a much larger per-read JSON Lines file. Preserve the distinction between technical runs and biological replicates; this toolkit does not infer that study design.

## Reuse and attribution

The subset is archived sequence data, separate from the MIT-licensed project code. It is redistributed under the [ENA/INSDC data-sharing policy](https://ena-browser-docs.readthedocs.io/en/latest/about/policies.html), which provides free and unrestricted access and reuse while asking for appropriate scientific attribution. We do not relabel the data as MIT or claim it was generated for this project. The archive also distinguishes public availability from a guarantee of record accuracy and discusses current access/benefit-sharing considerations; refer to the linked policy for its full terms.

Please retain the accession, source links, provenance record, and original study citation when reusing this excerpt. The other example FASTA/FASTQ files were written for this project and have no biological origin.
