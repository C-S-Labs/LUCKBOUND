"""Rebuild the diagnostic scenery module from the effective mapping, without uploading."""
from pathlib import Path
import json


def main():
    root = Path(__file__).resolve().parent
    mapping = json.loads((root / "unique_asset_mapping.json").read_text(encoding="utf-8"))
    ids = mapping["ids"]
    assert len(ids) == 61 and all(value.startswith("rbxassetid://") for value in ids.values())
    payload = json.dumps(ids, separators=(",", ":"))
    (root / "UniqueSceneryData.luau").write_text(
        '--!strict\n-- NON-PRODUCTION: 59 new IDs plus two accepted tree fallbacks.\n'
        'return game:GetService("HttpService"):JSONDecode(\n\t[==[' + payload + ']==]\n)\n',
        encoding="utf-8", newline="\n",
    )


if __name__ == "__main__":
    main()
