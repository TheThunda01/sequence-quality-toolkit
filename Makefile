.PHONY: demo test
demo:
	python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir reports --dataset-label "Synthetic teaching fixture; not observed biological data"
test:
	python -m unittest discover -s tests -v
