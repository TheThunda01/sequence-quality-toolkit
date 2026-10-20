.PHONY: demo test
demo:
	python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir reports --dataset-label "Synthetic teaching fixture; not observed biological data"
	python fastq_qc.py --manifest examples/fastq/samples.csv --output-dir reports/fastq_synthetic --dataset-label "Synthetic test reads; no biological origin"
	python fastq_qc.py --manifest examples/public/samples.csv --output-dir reports/fastq_public --dataset-label "First 1000 archived reads of yeast RNA-seq run ERR458493; convenience prefix, not representative"
test:
	python -m unittest discover -s tests -v
