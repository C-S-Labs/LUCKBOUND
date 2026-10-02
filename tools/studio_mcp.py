"""Small stdio MCP client for the local Roblox Studio benchmark connection."""
import argparse
import json
import os
import queue
import subprocess
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tool", nargs="?")
    parser.add_argument("--args", default="{}")
    parser.add_argument("--args-file")
    args = parser.parse_args()
    launcher = os.path.join(os.environ["LOCALAPPDATA"], "Roblox", "mcp.bat")
    process = subprocess.Popen(
        ["cmd.exe", "/c", launcher], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
    )
    output = queue.Queue()
    def reader():
        for line in process.stdout:
            try:
                output.put(json.loads(line))
            except json.JSONDecodeError:
                pass
    threading.Thread(target=reader, daemon=True).start()
    def send(value):
        process.stdin.write(json.dumps(value) + "\n")
        process.stdin.flush()
    def request(ident, method, params):
        send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            response = output.get(timeout=max(0.1, deadline - time.monotonic()))
            if response.get("id") == ident:
                return response
        raise TimeoutError(method)
    try:
        result = request(1, "initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "luckbound-generation-benchmark", "version": "1"},
        })
        if "error" in result:
            print(json.dumps(result))
            return
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        if args.tool:
            arguments = json.loads(open(args.args_file, encoding="utf-8-sig").read()
                                   if args.args_file else args.args)
            result = request(2, "tools/call", {"name": args.tool, "arguments": arguments})
        else:
            result = request(2, "tools/list", {})
        if not args.tool and "result" in result:
            result["result"]["tools"] = [
                tool for tool in result["result"]["tools"]
                if tool["name"] in {"list_roblox_studios", "get_studio_state", "execute_luau", "start_stop_play", "get_console_output", "screen_capture"}
            ]
        print(json.dumps(result, ensure_ascii=True))
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
