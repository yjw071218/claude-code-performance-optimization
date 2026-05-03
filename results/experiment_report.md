# MCP Scalability Experiment Report

## Experiment Setup
- Seed: 20260503
- Trials per point: 25
- Server scaling: context fixed at 256KB, servers in [1, 5, 10, 20, 30, 40, 50]
- Context scaling: servers fixed at 20, context in [64, 128, 256, 512, 1024] KB

## Server Scaling (Baseline)
| Servers | Mean Latency (ms) | P95 (ms) | Mean Peak Memory (MB) | Mean Tokens |
|---:|---:|---:|---:|---:|
| 1 | 41.61 | 46.51 | 2.514 | 37450 |
| 5 | 46.34 | 46.86 | 2.528 | 37450 |
| 10 | 61.81 | 62.51 | 2.561 | 37450 |
| 20 | 77.23 | 78.21 | 2.626 | 37450 |
| 30 | 92.64 | 93.25 | 2.692 | 37450 |
| 40 | 122.44 | 124.27 | 2.757 | 37450 |
| 50 | 139.11 | 139.77 | 2.823 | 37450 |


## Server Scaling (Optimized)
| Servers | Mean Latency (ms) | P95 (ms) | Mean Peak Memory (MB) | Mean Tokens |
|---:|---:|---:|---:|---:|
| 1 | 30.91 | 31.33 | 1.129 | 13108 |
| 5 | 30.95 | 31.28 | 1.130 | 13108 |
| 10 | 30.89 | 31.06 | 1.137 | 13108 |
| 20 | 46.41 | 47.09 | 1.157 | 13108 |
| 30 | 61.89 | 62.57 | 1.176 | 13108 |
| 40 | 76.04 | 77.59 | 1.196 | 13108 |
| 50 | 77.81 | 77.95 | 1.216 | 13108 |


## Context Scaling (Baseline)
| Context (KB) | Mean Latency (ms) | P95 (ms) | Mean Peak Memory (MB) | Mean Tokens |
|---:|---:|---:|---:|---:|
| 64 | 61.90 | 62.53 | 0.740 | 9363 |
| 128 | 61.72 | 62.37 | 1.368 | 18726 |
| 256 | 77.25 | 78.01 | 2.626 | 37450 |
| 512 | 97.57 | 108.02 | 5.147 | 74899 |
| 1024 | 170.27 | 171.36 | 10.197 | 149797 |


## Context Scaling (Optimized)
| Context (KB) | Mean Latency (ms) | P95 (ms) | Mean Peak Memory (MB) | Mean Tokens |
|---:|---:|---:|---:|---:|
| 64 | 44.50 | 47.00 | 0.313 | 3277 |
| 128 | 46.49 | 47.03 | 0.592 | 6554 |
| 256 | 46.38 | 47.05 | 1.157 | 13108 |
| 512 | 62.00 | 62.65 | 2.288 | 26215 |
| 1024 | 93.02 | 93.68 | 4.553 | 52430 |


## Key Findings
- Baseline latency slope after 10 servers: 1.998 ms/server
- 50-server latency reduction (optimized vs baseline): 44.06%
- 1024KB context latency reduction: 45.37%
