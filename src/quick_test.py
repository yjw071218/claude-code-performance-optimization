#!/usr/bin/env python3
"""Quick test of advanced optimization benchmark."""

import json
import csv
import time
import statistics
from advanced_optimization_benchmark import (
    MCPProtocolSimulator, OptimizationProfile, create_optimization_profiles
)

# Quick test with fewer trials
print("\n🧪 QUICK TEST (5 trials, 3 strategies)\n")

profiles = [
    OptimizationProfile("Baseline"),
    OptimizationProfile(
        "OPT-Full",
        context_compression_enabled=True,
        async_discovery_enabled=True,
        manifest_caching_enabled=True
    ),
    OptimizationProfile(
        "ULTRA",
        context_compression_enabled=True,
        context_compression_ratio=0.35,
        async_discovery_enabled=True,
        manifest_caching_enabled=True,
        incremental_manifests_enabled=True,
        connection_pooling_enabled=True,
        batch_discovery_enabled=True,
        predictive_caching_enabled=True,
        lazy_validation_enabled=True
    ),
]

results = []

for profile in profiles:
    print(f"Testing {profile.name}...")
    latencies = []
    
    for servers in [20]:
        for trial in range(5):
            sim = MCPProtocolSimulator(servers, 256, seed=20260503 + trial)
            result = sim.simulate_request(profile)
            latencies.append(result['total_latency_ms'])
            results.append({
                'profile': str(profile),
                'servers': servers,
                'trial': trial + 1,
                'latency_ms': result['total_latency_ms'],
                'tokens': result['token_count'],
            })
    
    print(f"  Mean: {statistics.mean(latencies):.2f}ms, "
          f"P95: {sorted(latencies)[int(0.95*len(latencies))]:.2f}ms")

print("\n✅ Quick test complete!\n")

# Display comparison
baseline_mean = statistics.mean([r['latency_ms'] for r in results if 'Baseline' in r['profile']])
best_result = min(results, key=lambda x: x['latency_ms'])
best_profile = best_result['profile']
best_latency = best_result['latency_ms']

improvement = (baseline_mean - best_latency) / baseline_mean * 100
print(f"Baseline (avg):     {baseline_mean:.2f}ms")
print(f"Best ({best_profile}): {best_latency:.2f}ms")
print(f"Improvement:        {improvement:.1f}%\n")
