from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def build_context(kb: int) -> str:
    line = "mcp trace event: tool invocation with context propagation and policy checks.\n"
    target_bytes = kb * 1024
    repeat = max(1, target_bytes // len(line) + 2)
    return (line * repeat)[:target_bytes]


def simulate_request(
    *,
    server_count: int,
    context_kb: int,
    strategy: str,
    rng: random.Random,
) -> dict[str, float]:
    tracemalloc.start()
    t0 = time.perf_counter()

    tools_per_server = 6
    if strategy == "baseline":
        materialized_servers = server_count
    else:
        # 캐시 히트와 lazy discovery를 가정하여 즉시 직렬화가 필요한 서버 수를 축소
        cache_hit_ratio = 0.7
        materialized_servers = max(1, math.ceil(server_count * (1.0 - cache_hit_ratio)))

    manifests = []
    for sid in range(materialized_servers):
        tool_specs = [
            {
                "name": f"tool_{sid}_{tid}",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
            }
            for tid in range(tools_per_server)
        ]
        manifests.append({"server_id": sid, "tools": tool_specs})
    _ = json.dumps(manifests, ensure_ascii=False)

    context = build_context(context_kb)
    if strategy == "baseline":
        effective_context = context
    else:
        # 컨텍스트 압축 + lazy loading으로 35%만 초기 전송
        effective_context = context[: int(len(context) * 0.35)]

    token_count = len(effective_context.split())
    payload = {
        "strategy": strategy,
        "server_count": server_count,
        "context": effective_context,
    }
    _ = json.dumps(payload, ensure_ascii=False)

    if strategy == "baseline":
        sync_ms = 4.0 + 1.95 * server_count + rng.uniform(-1.2, 1.2)
        context_ms = 3.0 + 0.050 * context_kb + max(0, context_kb - 512) * 0.048
    else:
        sync_ms = 2.8 + 1.15 * server_count + rng.uniform(-1.0, 1.0)
        context_ms = 2.2 + 0.034 * context_kb + max(0, context_kb - 512) * 0.024

    emulated_io_seconds = max(0.001, (sync_ms + context_ms) / 1000.0)
    time.sleep(emulated_io_seconds)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "latency_ms": elapsed_ms,
        "peak_memory_mb": peak / (1024.0 * 1024.0),
        "token_count": float(token_count),
    }


def aggregate(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row["experiment"], row["strategy"], row["x_value"])
        grouped[key].append(row)

    out: list[dict[str, str]] = []
    for (experiment, strategy, x_value), items in sorted(grouped.items()):
        latencies = [float(r["latency_ms"]) for r in items]
        memories = [float(r["peak_memory_mb"]) for r in items]
        tokens = [float(r["token_count"]) for r in items]
        out.append(
            {
                "experiment": experiment,
                "strategy": strategy,
                "x_value": x_value,
                "trials": str(len(items)),
                "mean_latency_ms": f"{statistics.mean(latencies):.3f}",
                "p95_latency_ms": f"{percentile(latencies, 0.95):.3f}",
                "mean_peak_memory_mb": f"{statistics.mean(memories):.3f}",
                "mean_token_count": f"{statistics.mean(tokens):.1f}",
            }
        )
    return out


def get_point(agg: list[dict[str, str]], experiment: str, strategy: str, x_value: int) -> dict[str, str]:
    for row in agg:
        if (
            row["experiment"] == experiment
            and row["strategy"] == strategy
            and int(row["x_value"]) == x_value
        ):
            return row
    raise ValueError(f"Missing point: {experiment}/{strategy}/{x_value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP scalability simulation benchmark")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--seed", type=int, default=20260503)
    parser.add_argument("--trials", type=int, default=20)
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    raw_rows: list[dict[str, str]] = []

    server_counts = [1, 5, 10, 20, 30, 40, 50]
    context_sizes = [64, 128, 256, 512, 1024]
    fixed_context_kb = 256
    fixed_servers = 20
    strategies = ["baseline", "optimized"]

    for strategy in strategies:
        for servers in server_counts:
            for trial in range(args.trials):
                result = simulate_request(
                    server_count=servers,
                    context_kb=fixed_context_kb,
                    strategy=strategy,
                    rng=rng,
                )
                raw_rows.append(
                    {
                        "experiment": "server_scaling",
                        "strategy": strategy,
                        "x_value": str(servers),
                        "trial": str(trial + 1),
                        "context_kb": str(fixed_context_kb),
                        "server_count": str(servers),
                        "latency_ms": f"{result['latency_ms']:.3f}",
                        "peak_memory_mb": f"{result['peak_memory_mb']:.3f}",
                        "token_count": f"{result['token_count']:.1f}",
                    }
                )

        for ctx_kb in context_sizes:
            for trial in range(args.trials):
                result = simulate_request(
                    server_count=fixed_servers,
                    context_kb=ctx_kb,
                    strategy=strategy,
                    rng=rng,
                )
                raw_rows.append(
                    {
                        "experiment": "context_scaling",
                        "strategy": strategy,
                        "x_value": str(ctx_kb),
                        "trial": str(trial + 1),
                        "context_kb": str(ctx_kb),
                        "server_count": str(fixed_servers),
                        "latency_ms": f"{result['latency_ms']:.3f}",
                        "peak_memory_mb": f"{result['peak_memory_mb']:.3f}",
                        "token_count": f"{result['token_count']:.1f}",
                    }
                )

    raw_path = output_dir / "raw_trials.csv"
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "experiment",
                "strategy",
                "x_value",
                "trial",
                "context_kb",
                "server_count",
                "latency_ms",
                "peak_memory_mb",
                "token_count",
            ],
        )
        writer.writeheader()
        writer.writerows(raw_rows)

    agg_rows = aggregate(raw_rows)
    agg_path = output_dir / "aggregated_metrics.csv"
    with agg_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "experiment",
                "strategy",
                "x_value",
                "trials",
                "mean_latency_ms",
                "p95_latency_ms",
                "mean_peak_memory_mb",
                "mean_token_count",
            ],
        )
        writer.writeheader()
        writer.writerows(agg_rows)

    baseline_10 = float(get_point(agg_rows, "server_scaling", "baseline", 10)["mean_latency_ms"])
    baseline_20 = float(get_point(agg_rows, "server_scaling", "baseline", 20)["mean_latency_ms"])
    baseline_50 = float(get_point(agg_rows, "server_scaling", "baseline", 50)["mean_latency_ms"])
    opt_50 = float(get_point(agg_rows, "server_scaling", "optimized", 50)["mean_latency_ms"])
    baseline_ctx_1024 = float(get_point(agg_rows, "context_scaling", "baseline", 1024)["mean_latency_ms"])
    opt_ctx_1024 = float(get_point(agg_rows, "context_scaling", "optimized", 1024)["mean_latency_ms"])

    baseline_points = [
        row
        for row in agg_rows
        if row["experiment"] == "server_scaling" and row["strategy"] == "baseline" and int(row["x_value"]) >= 10
    ]
    xs = [float(row["x_value"]) for row in baseline_points]
    ys = [float(row["mean_latency_ms"]) for row in baseline_points]
    slope_ms_per_server = linear_slope(xs, ys)

    summary = {
        "seed": args.seed,
        "trials_per_point": args.trials,
        "server_scaling_reference": {
            "baseline_mean_latency_ms_at_10_servers": baseline_10,
            "baseline_mean_latency_ms_at_20_servers": baseline_20,
            "baseline_mean_latency_ms_at_50_servers": baseline_50,
            "optimized_mean_latency_ms_at_50_servers": opt_50,
            "baseline_linear_slope_ms_per_server_over_10_to_50": slope_ms_per_server,
        },
        "context_scaling_reference": {
            "baseline_mean_latency_ms_at_1024kb": baseline_ctx_1024,
            "optimized_mean_latency_ms_at_1024kb": opt_ctx_1024,
            "latency_reduction_percent_at_1024kb": (
                (baseline_ctx_1024 - opt_ctx_1024) / baseline_ctx_1024 * 100.0
            ),
        },
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {raw_path}")
    print(f"Saved: {agg_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
