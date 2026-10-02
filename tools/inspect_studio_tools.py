"""Print selected schema without dumping the full MCP catalogue."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
value=json.loads((root/'.tools/studio_tools.json').read_text(encoding='utf-16'))
for tool in value['result']['tools']:
    if tool['name'] in {'screen_capture','execute_luau','get_console_output'}:
        print(json.dumps(tool))
