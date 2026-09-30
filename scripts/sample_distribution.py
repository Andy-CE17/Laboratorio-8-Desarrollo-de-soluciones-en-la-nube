"""Cuenta instancias observadas por el balanceador: python scripts/sample_distribution.py 100"""
import collections
import json
import sys
import urllib.request

total = int(sys.argv[1]) if len(sys.argv) > 1 else 30
url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1/instance/"
counts = collections.Counter()
failures = 0
for _ in range(total):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            counts[json.load(response)["instance"]] += 1
    except Exception as exc:
        failures += 1
        print(f"Fallo: {exc}", file=sys.stderr)
for name in sorted(counts):
    print(f"{name}: {counts[name]} ({counts[name] / total * 100:.1f}%)")
print(f"Fallos: {failures}")
