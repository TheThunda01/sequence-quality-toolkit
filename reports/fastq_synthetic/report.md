# FASTQ quality summary

Dataset label supplied by the caller: Synthetic test reads; no biological origin

All samples were explicitly declared Phred+33. No reads were changed or filtered.

| Sample | Reads | Bases | Mean Phred (base weighted) | Q30 fraction | N fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| toy_sample_A | 3 | 18 | 28.889 | 0.6667 | 0.1111 |
| toy_sample_B | 2 | 10 | 18.000 | 0.3000 | 0.4000 |

Q20 and Q30 are descriptive score thresholds, not validated acceptance rules. Quality scores are base-caller estimates; they do not measure alignment quality, contamination, organism identity, or biological function.

Cycle summaries use only reads reaching that cycle. These outputs describe the provided files, not an entire experiment unless those files are complete and appropriately selected.

Read-level results are in `read_metrics.jsonl`; sample-level values in `samples.csv`; per-cycle summaries in `cycles.csv`; exact length counts in `length_distribution.csv`. Input fingerprints and quality histograms are in `report.json`.
