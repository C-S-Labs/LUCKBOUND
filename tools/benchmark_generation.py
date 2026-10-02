"""Run actual Luau layout source, save raw samples and summarize CPU-only results."""
import argparse
import csv
import importlib.util
import json
import statistics
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--luau', default='.tools/luau/luau.exe')
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('suite', root / 'tests/build_suite.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)
suite.main()
bundle = (root / 'tests/generated_suite.luau').read_text(encoding='utf-8').split('-- === test cases ===')[0]
target = root / '.tools/generation_headless.luau'
target.write_text(bundle + (root / 'tests/generation_performance.luau').read_text(encoding='utf-8'), encoding='utf-8')
result = subprocess.run([args.luau, str(target)], cwd=root, capture_output=True, text=True, check=True)
rows = list(csv.reader(line for line in result.stdout.splitlines() if ',' in line))
output = root / 'docs/benchmarks'
output.mkdir(exist_ok=True)
with (output / 'generation_headless.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['stage', 'world', 'seed', 'layout_seconds', 'success', 'assembly_attempts', 'candidate_attempts', 'overlap_comparisons'])
    writer.writerows(rows)
summary = {}
for stage in 'ABCDEF':
    selected = [row for row in rows if row[0] == stage]
    times = [float(row[3]) for row in selected]
    summary[stage] = {'runs': len(selected), 'median_layout_ms': statistics.median(times) * 1000,
                      'worst_layout_ms': max(times) * 1000,
                      'assembly_failures': sum(row[4] != 'true' for row in selected)}
(output / 'generation_headless.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(result.stdout.splitlines()[-1])
print(json.dumps(summary, indent=2))
