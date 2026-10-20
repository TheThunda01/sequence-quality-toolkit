# FASTQ quality summary

Dataset label supplied by the caller: First 1000 archived reads of yeast RNA-seq run ERR458493; convenience prefix, not representative

All samples were explicitly declared Phred+33. No reads were changed or filtered.

| Sample | Reads | Bases | Mean Phred (base weighted) | Q30 fraction | N fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| ERR458493_prefix | 1000 | 51000 | 37.015 | 0.9444 | 0.0000 |

Q20 and Q30 are descriptive score thresholds, not validated acceptance rules. Quality scores are base-caller estimates; they do not measure alignment quality, contamination, organism identity, or biological function.

Cycle summaries use only reads reaching that cycle. These outputs describe the provided files, not an entire experiment unless those files are complete and appropriately selected.

Read-level results are in `read_metrics.jsonl`; sample-level values in `samples.csv`; per-cycle summaries in `cycles.csv`; exact length counts in `length_distribution.csv`. Input fingerprints and quality histograms are in `report.json`.
