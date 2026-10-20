"""Rebuild the fixed 1,000-read teaching subset from verified ENA bytes."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from urllib.request import urlopen

SOURCE_URL = "https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR458/ERR458493/ERR458493.fastq.gz"
SOURCE_MD5 = "2b8c708cce1fd88e7ddecd51e5ae2154"
SOURCE_BYTES = 59532325
RECORDS = 1000


def subset(source: Path, output_dir: Path) -> dict:
    digest = hashlib.md5()
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if source.stat().st_size != SOURCE_BYTES or digest.hexdigest() != SOURCE_MD5:
        raise ValueError("Source does not match the recorded ENA file size and MD5; no subset was written")
    pieces = []
    with gzip.open(source, "rb") as handle:
        for record in range(RECORDS):
            block = [handle.readline() for _ in range(4)]
            if any(not line for line in block) or not block[0].startswith(b"@") or not block[2].startswith(b"+"):
                raise ValueError(f"Unexpected archive FASTQ layout at record {record + 1}")
            if len(block[1].rstrip(b"\r\n")) != len(block[3].rstrip(b"\r\n")):
                raise ValueError("Source sequence/quality length mismatch")
            pieces.extend(block)
    data = b"".join(pieces)
    compressed = io.BytesIO()
    # Fixed timestamp and empty stored filename make the gzip deterministic.
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0, compresslevel=9) as handle:
        handle.write(data)
    filename = "ERR458493_first1000.fastq.gz"
    metadata = {
        "run_accession": "ERR458493", "project_accession": "PRJEB5348",
        "source_organism_label": "Saccharomyces cerevisiae",
        "source_layout": "SINGLE", "source_strategy": "RNA-Seq",
        "source_url": SOURCE_URL, "source_bytes": SOURCE_BYTES, "source_md5": SOURCE_MD5,
        "metadata_url": "https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERR458493&result=read_run&fields=run_accession,scientific_name,library_layout,fastq_ftp,fastq_md5,fastq_bytes&format=tsv",
        "archive_metadata_recorded_utc_date": "2026-10-20",
        "source_integrity_check": "The complete source file size and MD5 are verified on every extraction",
        "selection": "First 1000 records in archive order, preserving their original four-line record bytes",
        "sampling_warning": "A convenience prefix, not random or representative of this run or experiment",
        "records": RECORDS, "subset_filename": filename,
        "subset_compressed_sha256": hashlib.sha256(compressed.getvalue()).hexdigest(),
        "subset_uncompressed_sha256": hashlib.sha256(data).hexdigest(),
        "first_read_id": pieces[0].decode("ascii").strip()[1:].split()[0],
        "last_read_id": pieces[-4].decode("ascii").strip()[1:].split()[0],
        "quality_encoding": "phred33",
        "encoding_basis": "ENA archive-generated FASTQ convention: https://ena-docs.readthedocs.io/en/latest/retrieval/file-download/archive-generated-files.html",
        "study_publication_doi": "10.1261/rna.053959.115",
        "data_terms": "ENA/INSDC data-sharing policy; not relicensed under this project's MIT code license",
        "data_terms_url": "https://ena-browser-docs.readthedocs.io/en/latest/about/policies.html",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / filename).write_bytes(compressed.getvalue())
    (output_dir / "provenance.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", type=Path, help="Use a local copy of the complete ENA gzip instead of downloading")
    parser.add_argument("--output-dir", type=Path, default=Path("examples/public"))
    args = parser.parse_args()
    if args.source_file:
        metadata = subset(args.source_file, args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="sequence_qc_source_") as tmp:
            source = Path(tmp) / "source.fastq.gz"
            print(f"Downloading {SOURCE_BYTES:,} bytes from ENA for checksum verification")
            with urlopen(SOURCE_URL, timeout=60) as response, source.open("wb") as handle:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    handle.write(block)
            metadata = subset(source, args.output_dir)
    print(f"Wrote {metadata['records']} records; gzip SHA-256 {metadata['subset_compressed_sha256']}")


if __name__ == "__main__":
    main()
