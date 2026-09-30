"""Comparación simple de latencia y rendimiento en /health/."""
import concurrent.futures
import statistics
import sys
import time
import urllib.request

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1/health/"
total = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 50


def call(_):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            response.read()
            return response.status == 200, time.perf_counter() - started
    except Exception:
        return False, time.perf_counter() - started


started = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
    results = list(pool.map(call, range(total)))
elapsed = time.perf_counter() - started
latencies = [duration * 1000 for _, duration in results]
failures = sum(not success for success, _ in results)
print(f"URL: {url}")
print(f"Peticiones: {total} | Concurrencia: {concurrency}")
print(f"Tiempo total: {elapsed:.2f} s")
print(f"Peticiones/s: {total / elapsed:.2f}")
print(f"Latencia promedio: {statistics.mean(latencies):.2f} ms")
print(f"Fallos: {failures}")
