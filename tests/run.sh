#!/usr/bin/env bash
# Builds and runs the LUCKBOUND headless test suite.
# Requires the `luau` CLI: https://github.com/luau-lang/luau/releases
set -euo pipefail
cd "$(dirname "$0")/.."

command -v luau >/dev/null 2>&1 || {
	echo "error: 'luau' not on PATH. Download it from"
	echo "       https://github.com/luau-lang/luau/releases"
	exit 1
}

python3 tests/build_suite.py
luau tests/generated_suite.luau
