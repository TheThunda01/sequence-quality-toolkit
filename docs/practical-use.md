# Practical use

## Where this fits

Use this toolkit to inspect declared sequence files before a downstream analysis and to learn exactly how basic QC quantities are calculated. The new input fingerprint command addresses a simple handoff problem: the file later analyzed may differ from the file originally received. It records and rechecks raw bytes independently of sequence parsing.

This distinction matters. A fingerprint can detect a changed download or sample sheet; the FASTQ parser checks file structure; a paired-file check tests positional naming; biological interpretation requires additional evidence. Passing one does not imply passing the others.

## Input and output contract

`input_fingerprints.py` accepts the same three-column FASTQ sample sheet as `fastq_qc.py`: `sample_id,fastq_path,quality_encoding`. Paths are relative to the sample sheet. Existing validation requires unique sample IDs and resolved files, existing inputs, and an explicit `phred33` declaration.

`create` writes a new JSON lock containing the sample-sheet SHA-256 and each sample's relative path, encoding, raw byte count, and SHA-256. For gzip input, these are compressed-file bytes. It refuses an existing lock and will not overwrite the sample sheet or an input. `verify` reads that lock and compares every recorded field against a fresh scan. Expected errors return exit code 2; success returns 0. Neither operation writes, trims, or parses the FASTQ input.

The QC command now accepts optional `--input-lock PATH`. It verifies the lock before processing, compares the raw-byte hashes actually consumed by the parser with that lock, and checks that the sample sheet and lock did not change during processing. All these checks occur before replacing reports. Lock failure returns exit code 2 and leaves earlier report files unchanged. The lock path itself is protected from output overwrite. With this flag, `report.json` adds an `input_lock` object containing the lock filename, SHA-256, status, and scope. Without it, existing behavior and report structure are unchanged.

The supplied [public input lock](../examples/public/input-lock.json) pins the included 1,000-read yeast excerpt. It does not pin or validate the entire archived run. The original [public provenance record](public-data.md) separately documents verification of the complete download before subset creation.

## Worked use case

Check the shipped excerpt, then run its structural and quality summaries:

```sh
python fastq_qc.py --manifest examples/public/samples.csv --input-lock examples/public/input-lock.json --output-dir my-qc --dataset-label "First 1000 archived reads of ERR458493; convenience prefix, not representative"
```

For your own already obtained files, create the lock after independently establishing their source and intended sample mapping:

```sh
python input_fingerprints.py create --manifest my-samples.csv --lock my-input-lock.json
python fastq_qc.py --manifest my-samples.csv --input-lock my-input-lock.json --output-dir my-qc
```

Keep the lock with the sample sheet when transferring data. A renamed sample, changed path, modified quality string, or truncated file will fail verification. Recompressing identical reads can also fail because gzip bytes change; that is intentional byte-level behavior, not evidence that the biological content changed.

## Checks before relying on a result

The operator chooses the correct source, mapping, and encoding; the lock does not discover them. Check archive provenance where available, then use the appropriate parser and optional paired check. Prefer the integrated flag when producing QC reports. Its second check binds reported metrics to the raw bytes read by the parser, but it does not lock the filesystem or promise that files remain unchanged afterward. Avoid concurrent edits. Separate `input_fingerprints.py verify` remains useful during transfer, with a gap between that check and any later processing.

Interpret the public example only as a convenience prefix. Its average Phred score is not an observed error rate, and its high-Q fraction does not establish organism identity, lack of contamination, or suitability for a downstream assay. The paired examples are synthetic, while the public yeast example is single-end.

## Known limits

The lock is not signed or authenticated and can be replaced together with the data. It can faithfully fingerprint malformed or empty input; the QC parser still rejects unsuitable FASTQ before publishing. It does not validate biological sample identity or correct mate pairing. The integrated preflight adds a sequential read of each file, and JSONL metrics may be large. There is no filesystem-wide transaction: an operating-system failure during final file replacements can still leave a partial report set, so check the exit status. The toolkit still lacks adapter identification, trimming, mapping, duplication assessment, and contamination screening.

## Next improvements

1. **Portable report schema:** publish versioned JSON schemas; acceptance means valid current examples pass and missing required fields fail in automated tests.
2. **Paired-input handoff:** extend a separately versioned lock to explicit R1/R2 assignments; acceptance means swapped mate declarations fail while current naming checks remain unchanged.
3. **Cross-platform checks:** run the parser and lock tests on Windows and Linux; acceptance means identical input bytes yield identical metrics and lock records without path-specific leakage.
4. **Complete-bundle publication:** make the final output set replaceable as one directory transaction under a documented contract; acceptance means simulated replacement failures leave the prior complete bundle recoverable.
