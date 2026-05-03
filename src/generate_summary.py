#!/usr/bin/env python3
"""
Generate summary statistics and visualizations from benchmark results
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

def analyze_results():
    """Analyze benchmark results and generate summary"""
    
    results_dir = Path("results")
    csv_file = results_dir / "aggregated_metrics.csv"
    
    if not csv_file.exists():
        print(f"❌ Results file not found: {csv_file}")
        return
    
    # Read CSV data
    data = defaultdict(lambda: defaultdict(list))
    with open(csv_file) as f:
        for row in csv.DictReader(f):
            experiment = row['experiment']  # Changed from 'scenario'
            strategy = row['strategy']
            x_val = row['x_value']
            latency = float(row['mean_latency_ms'])
            data[experiment][strategy].append((int(x_val), latency))
    
    # Sort by x value
    for experiment in data:
        for strategy in data[experiment]:
            data[experiment][strategy].sort()
    
    # Generate summary report
    print("\n" + "="*70)
    print("📊 MCP PERFORMANCE OPTIMIZATION - BENCHMARK SUMMARY")
    print("="*70)
    
    # Server Scaling Results
    print("\n### Server Scaling (256KB context, 20 servers per iteration)")
    print("-" * 70)
    baseline_50 = None
    optimized_50 = None
    
    for servers, latency in data['server_scaling']['baseline']:
        if servers == 50:
            baseline_50 = latency
            print(f"Baseline (50 servers):  {latency:7.2f}ms")
    
    for servers, latency in data['server_scaling']['optimized']:
        if servers == 50:
            optimized_50 = latency
            print(f"Optimized (50 servers): {latency:7.2f}ms")
    
    if baseline_50 and optimized_50:
        improvement = (baseline_50 - optimized_50) / baseline_50 * 100
        print(f"Improvement:            {improvement:7.2f}%")
    
    # Context Scaling Results
    print("\n### Context Scaling (20 servers, 64KB-1024KB)")
    print("-" * 70)
    baseline_1024 = None
    optimized_1024 = None
    
    for ctx_size, latency in data['context_scaling']['baseline']:
        if ctx_size == 1024:
            baseline_1024 = latency
            print(f"Baseline (1024KB):  {latency:7.2f}ms")
    
    for ctx_size, latency in data['context_scaling']['optimized']:
        if ctx_size == 1024:
            optimized_1024 = latency
            print(f"Optimized (1024KB): {latency:7.2f}ms")
    
    if baseline_1024 and optimized_1024:
        improvement = (baseline_1024 - optimized_1024) / baseline_1024 * 100
        print(f"Improvement:        {improvement:7.2f}%")
    
    print("\n" + "="*70)
    print("✅ Benchmark analysis complete!")
    print("📁 Results saved to: results/")
    print("="*70 + "\n")

if __name__ == "__main__":
    analyze_results()
