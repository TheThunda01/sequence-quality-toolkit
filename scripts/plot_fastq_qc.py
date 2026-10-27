"""Plot existing FASTQ summaries without reopening or changing sequence inputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def load_summary(directory: Path) -> tuple[dict, dict[str, list[dict]]]:
    """Validate identity and denominators before importing optional plotting code."""
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    if report.get("mode") != "fastq" or not report.get("dataset_label"):
        raise ValueError("Expected a labeled FASTQ report")
    samples = report["samples"]
    by_id = {sample["sample_id"]: sample for sample in samples}
    if len(by_id) != len(samples) or not samples or any(not isinstance(key, str) or not key for key in by_id):
        raise ValueError("Sample IDs must be unique and nonempty")
    rows = {key: [] for key in by_id}
    with (directory / "cycles.csv").open(newline="", encoding="utf-8") as stream:
        for raw in csv.DictReader(stream):
            sample_id = raw["sample_id"]
            if sample_id not in rows:
                raise ValueError("Cycle table contains an unknown sample ID")
            row = {"cycle": int(raw["cycle"]), "observed_bases": int(raw["observed_bases"]),
                   "mean_phred": float(raw["mean_phred"])}
            if not math.isfinite(row["mean_phred"]) or not 0 <= row["mean_phred"] <= 93:
                raise ValueError("Mean Phred must be finite and between 0 and 93")
            rows[sample_id].append(row)
    for key, sample in by_id.items():
        data = sorted(rows[key], key=lambda row: row["cycle"])
        rows[key] = data
        if [row["cycle"] for row in data] != list(range(1, sample["max_length"] + 1)):
            raise ValueError("Cycles must be unique and contiguous through max_length")
        counts = [row["observed_bases"] for row in data]
        if not counts or counts[0] != sample["read_count"] or any(c <= 0 for c in counts):
            raise ValueError("First-cycle denominator must equal the read count")
        if any(right > left for left, right in zip(counts, counts[1:])):
            raise ValueError("Cycle denominators cannot increase")
        if sum(counts) != sample["total_bases"]:
            raise ValueError("Cycle denominators must sum to total bases")
        weighted = sum(row["mean_phred"] * row["observed_bases"] for row in data) / sum(counts)
        if not math.isclose(weighted, sample["base_weighted_mean_phred"], abs_tol=1.1e-6, rel_tol=0):
            raise ValueError("Cycle-weighted quality disagrees with report.json")
    return report, rows


def render(directory: Path, output: Path) -> None:
    report, rows = load_summary(directory)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "fastq-cycle-context-v1"})
    figure, axes = plt.subplots(2, 1, figsize=(9.5, 6.3), sharex=True,
                               gridspec_kw={"height_ratios": [1.6, 1]}, layout="constrained")
    colors = plt.get_cmap("tab10")
    for index, (sample_id, data) in enumerate(rows.items()):
        x = [row["cycle"] for row in data]
        axes[0].plot(x, [row["mean_phred"] for row in data], marker="o", markersize=3,
                     label=sample_id, color=colors(index % 10))
        axes[1].step(x, [row["observed_bases"] for row in data], where="mid", label=sample_id,
                     color=colors(index % 10), linewidth=2)
    axes[0].set(ylabel="Mean Phred score", ylim=(0, 45))
    maximum = max(row["mean_phred"] for data in rows.values() for row in data)
    if maximum > 43:
        axes[0].set_ylim(0, maximum + 2)
    axes[0].legend(loc="best", frameon=False)
    axes[1].set(xlabel="Read position (1-based)", ylabel="Contributing reads", ylim=(0, None))
    axes[1].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))
    for axis in axes:
        axis.grid(axis="y", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Quality and its changing denominator", weight="bold", fontsize=16)
    axes[0].set_title(report["dataset_label"], fontsize=10, pad=13)
    figure.supxlabel("Only reads reaching a position contribute. A higher mean may reflect a different set of reads.", fontsize=9)
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "png"):
        figure.savefig(output / f"cycle-context.{suffix}", dpi=160,
                       metadata={"Date": None} if suffix == "svg" else None)
    plt.close(figure)
    provenance = {
        "schema_version": 1, "dataset_label": report["dataset_label"],
        "sources": [{"name": name, "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
                    for name in ("report.json", "cycles.csv")],
        "matplotlib_version": matplotlib.__version__,
        "samples": [{"sample_id": key, "cycles": len(data),
                     "first_cycle_reads": data[0]["observed_bases"], "last_cycle_reads": data[-1]["observed_bases"]}
                    for key, data in rows.items()],
        "scope": "Visualization of saved summaries; no new QC, error-rate measurement, or biological inference.",
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        render(args.report_dir, args.output_dir)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"Invalid summary: {exc}\n")


if __name__ == "__main__":
    main()
