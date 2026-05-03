from __future__ import annotations

import csv
import json
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pick(rows: list[dict[str, str]], experiment: str, strategy: str) -> list[dict[str, str]]:
    out = [r for r in rows if r["experiment"] == experiment and r["strategy"] == strategy]
    return sorted(out, key=lambda r: int(r["x_value"]))


def to_table(rows: list[dict[str, str]], x_label: str) -> str:
    header = f"| {x_label} | Mean Latency (ms) | P95 (ms) | Mean Peak Memory (MB) | Mean Tokens |\n"
    sep = "|---:|---:|---:|---:|---:|\n"
    body = ""
    for r in rows:
        body += (
            f"| {r['x_value']} | {float(r['mean_latency_ms']):.2f} | "
            f"{float(r['p95_latency_ms']):.2f} | {float(r['mean_peak_memory_mb']):.3f} | "
            f"{float(r['mean_token_count']):.0f} |\n"
        )
    return header + sep + body


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results"
    agg_path = results_dir / "aggregated_metrics.csv"
    summary_path = results_dir / "summary.json"

    rows = load_rows(agg_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    server_baseline = pick(rows, "server_scaling", "baseline")
    server_optimized = pick(rows, "server_scaling", "optimized")
    context_baseline = pick(rows, "context_scaling", "baseline")
    context_optimized = pick(rows, "context_scaling", "optimized")

    lines: list[str] = []
    lines.append("# MCP Scalability Experiment Report")
    lines.append("")
    lines.append("## Experiment Setup")
    lines.append("- Seed: {}".format(summary["seed"]))
    lines.append("- Trials per point: {}".format(summary["trials_per_point"]))
    lines.append("- Server scaling: context fixed at 256KB, servers in [1, 5, 10, 20, 30, 40, 50]")
    lines.append("- Context scaling: servers fixed at 20, context in [64, 128, 256, 512, 1024] KB")
    lines.append("")
    lines.append("## Server Scaling (Baseline)")
    lines.append(to_table(server_baseline, "Servers"))
    lines.append("")
    lines.append("## Server Scaling (Optimized)")
    lines.append(to_table(server_optimized, "Servers"))
    lines.append("")
    lines.append("## Context Scaling (Baseline)")
    lines.append(to_table(context_baseline, "Context (KB)"))
    lines.append("")
    lines.append("## Context Scaling (Optimized)")
    lines.append(to_table(context_optimized, "Context (KB)"))
    lines.append("")
    lines.append("## Key Findings")
    lines.append(
        "- Baseline latency slope after 10 servers: {:.3f} ms/server".format(
            float(summary["server_scaling_reference"]["baseline_linear_slope_ms_per_server_over_10_to_50"])
        )
    )
    lines.append(
        "- 50-server latency reduction (optimized vs baseline): {:.2f}%".format(
            (
                float(summary["server_scaling_reference"]["baseline_mean_latency_ms_at_50_servers"])
                - float(summary["server_scaling_reference"]["optimized_mean_latency_ms_at_50_servers"])
            )
            / float(summary["server_scaling_reference"]["baseline_mean_latency_ms_at_50_servers"])
            * 100.0
        )
    )
    lines.append(
        "- 1024KB context latency reduction: {:.2f}%".format(
            float(summary["context_scaling_reference"]["latency_reduction_percent_at_1024kb"])
        )
    )

    report_path = results_dir / "experiment_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {report_path}")


if __name__ == "__main__":
    main()
