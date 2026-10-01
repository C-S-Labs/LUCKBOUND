"""Compare legacy chunk loading against the pre-multipart loader with an API contract shim.

This checks loading/placement calls, not Roblox collision cooking or physics. Studio remains required.
Run: python tests/check_chunk_loader.py --luau <luau executable>
"""
import argparse
import pathlib
import re
import subprocess
import build_suite

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--luau", default="luau")
parser.add_argument("--baseline", default="1001ec2", help="pre-multipart revision")
args = parser.parse_args()
build_suite.main()
bundle = (ROOT / "tests/generated_suite.luau").read_text(encoding="utf-8").split("-- === test cases ===")[0]
path = "src/shared/Util/ChunkLoader.luau"
old = subprocess.run(["git", "show", f"{args.baseline}:{path}"], cwd=ROOT,
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout
new = (ROOT / path).read_text(encoding="utf-8")

def loader_factory(name, source):
    source = re.sub(r"require\(Root\.\w+\.(\w+)\)", lambda m: f'__require("{m[1]}")', source)
    return f"local function {name}()\n{source}\nend\n"

shim = (ROOT / "tests/chunk_loader_contract.luau").read_text(encoding="utf-8")
setup, cases = shim.split("-- LOADER_FACTORIES --")
generated = ROOT / ".tools/generated_loader_contract.luau"
generated.parent.mkdir(exist_ok=True)
generated.write_text(bundle + setup + loader_factory("oldFactory", old) +
                     loader_factory("newFactory", new) + cases, encoding="utf-8")
subprocess.run([args.luau, str(generated)], cwd=ROOT, check=True)
