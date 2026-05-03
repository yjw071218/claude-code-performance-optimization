# MCP Performance Optimization - Experiment Guide

Guide for running, understanding, and extending the MCP optimization research experiments.

## Quick Start

```bash
# Run complete benchmark
python src/optimization_benchmark.py

# Analyze results
python src/analyze_optimization.py

# View results
cat results/optimization_analysis.md
```

**Duration:** ~10 minutes (4,800 trials)

---

## Experiment Overview

### What We Measure

1. **Response Latency (ms)**: End-to-end request processing time
2. **Peak Memory (MB)**: Maximum memory used during request
3. **Token Count**: LLM tokenization overhead (cost indicator)
4. **Throughput**: Requests/second capability

### Test Scenarios

#### Scenario 1: Server Scaling
- **Variable:** 1, 5, 10, 20, 30, 40, 50 servers
- **Fixed:** 256 KB context
- **Purpose:** Measure synchronization bottleneck
- **Expected Finding:** Linear latency growth at baseline, sublinear with optimization

#### Scenario 2: Context Scaling
- **Variable:** 64, 128, 256, 512, 1024 KB
- **Fixed:** 20 servers
- **Purpose:** Measure tokenization/serialization bottleneck
- **Expected Finding:** Super-linear degradation at baseline, linear with OPT1

### Configurations Tested

| Config | Compression | Async | Cache | Incremental | Pooling | Name |
|:--|:--:|:--:|:--:|:--:|:--:|:--|
| 1 | ❌ | ❌ | ❌ | ❌ | ❌ | Baseline |
| 2 | ✅ | ❌ | ❌ | ❌ | ❌ | OPT1 |
| 3 | ✅ | ✅ | ❌ | ❌ | ❌ | OPT1+2 |
| 4 | ✅ | ✅ | ✅ | ❌ | ❌ | OPT1+2+3 |
| 5 | ✅ | ✅ | ✅ | ✅ | ❌ | OPT1+2+3+4 |
| 6 | ✅ | ✅ | ✅ | ✅ | ✅ | OPT1+2+3+4+5 |

---

## Running the Benchmark

### Prerequisites

```bash
# Check Python version
python --version  # Must be 3.9+

# Navigate to project
cd C:\Artificial_Intelligence\mcp_scalability_research
```

### Full Benchmark

```bash
# Run all 6 configurations × 2 scenarios × 7/5 points × 20 trials = 4,800 trials
python src/optimization_benchmark.py

# Expected output:
# Running 6 optimization configurations...
# Trials: 20 | Seed: 20260503
# 📊 Baseline
# ├─ Server Scaling...
# ├─ Context Scaling...
# 📊 OPT1 (Context Compression)...
# ... [continues for all 6 configs]
# ✅ Benchmark complete!
# 📁 Results: results/
```

### Partial Benchmark (Faster Testing)

```bash
# Edit optimization_benchmark.py temporarily:
# Line ~380: change ALL_SCENARIOS
# From: ALL_SCENARIOS = ['server_scaling', 'context_scaling']
# To:   ALL_SCENARIOS = ['server_scaling']  # Only server scaling

python src/optimization_benchmark.py  # ~5 minutes
```

---

## Understanding Results

### Output Files

#### 1. `results/raw_trials.csv`
Raw data for all 4,800 trials.

#### 2. `results/aggregated_metrics.csv`
Statistical summaries per configuration/scenario/value.

#### 3. `results/summary.json`
Key findings and improvement percentages.

#### 4. `results/optimization_analysis.md`
Formatted markdown report of findings.

---

## Analyzing Results

### Using `analyze_optimization.py`

```bash
python src/analyze_optimization.py
```

### Manual Analysis

```python
import csv
import statistics

with open('results/raw_trials.csv') as f:
    reader = csv.DictReader(f)
    trials = list(reader)

# Filter by configuration
baseline = [t for t in trials if t['config_id'] == '0']

# Calculate mean
baseline_latency = statistics.mean(float(t['latency_ms']) for t in baseline)
print(f"Baseline mean: {baseline_latency:.1f}ms")
```

---

## Performance Regression Testing

### Baseline Comparison

```bash
# Save current results
cp results/aggregated_metrics.csv results/baseline_metrics.csv

# Re-run after changes
python src/optimization_benchmark.py
```

---

## Next Steps

1. **Validate:** Deploy optimizations on real MCP
2. **Extend:** Add new optimization techniques
3. **Publish:** Share findings in research community
4. **Optimize:** Fine-tune parameters based on real-world data

---

**Questions?** See OPTIMIZATION_TECHNIQUES.md for implementation details.
