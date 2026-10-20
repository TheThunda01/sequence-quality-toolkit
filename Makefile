.PHONY: demo test
demo:
	python sequence_qc.py --fasta examples/synthetic_sequences.fasta --manifest examples/manifest.csv --output-dir reports --dataset-label "Synthetic teaching fixture; not observed biological data"
	python fastq_qc.py --manifest examples/fastq/samples.csv --output-dir reports/fastq_synthetic --dataset-label "Synthetic test reads; no biological origin"
	python fastq_qc.py --manifest examples/public/samples.csv --output-dir reports/fastq_public --dataset-label "First 1000 archived reads of yeast RNA-seq run ERR458493; convenience prefix, not representative"
	python paired_fastq_check.py --read1 examples/paired/suffix_R1.fastq --read2 examples/paired/suffix_R2.fastq --name-convention suffix --quality-encoding phred33 --sample-id synthetic_suffix --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir reports/paired_suffix
	python paired_fastq_check.py --read1 examples/paired/illumina_R1.fastq --read2 examples/paired/illumina_R2.fastq --name-convention illumina --quality-encoding phred33 --sample-id synthetic_illumina --dataset-label "Synthetic paired fixtures; no biological origin" --output-dir reports/paired_illumina
test:
	python -m unittest discover -s tests -v
