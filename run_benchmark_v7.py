import benchmark
results = benchmark.run_benchmark(suite="all")
print(benchmark.format_results(results))
