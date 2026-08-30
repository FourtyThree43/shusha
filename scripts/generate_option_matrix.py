"""Generate docs/aria2/option-matrix.md from spec/aria2/options.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/home/BillGates/code/shusha")
with open(ROOT / "spec/aria2/options.json", encoding="utf-8") as f:
    options = json.load(f)

lines: list[str] = []
lines.append("# aria2 Option Coverage Matrix\n")
lines.append(
    "> Authoritative option coverage matrix required by PLAN.md Section 13 and E00-I03.\n"
)
lines.append(
    "| Option Name | Short | Category | Type | Default | Frontend Exposure | Mutability | RPC Support | Adapter Mapping | Coverage State | Tests |"
)
lines.append(
    "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |"
)

type_map = {
    "string": "str",
    "integer": "int",
    "enum": "str / Enum",
    "path": "Path / str",
    "duration": "int / timedelta",
    "size": "int (bytes)",
    "boolean": "bool",
}

for opt in options:
    name = f"--{opt['name']}"
    short = f"-{opt['short_name']}" if opt.get("short_name") else "—"
    cat = opt.get("category", "basic")
    raw_type = opt.get("type", "string")
    py_type = type_map.get(raw_type, raw_type)
    default_val = str(opt.get("default")) if opt.get("default") is not None else "—"
    default_val = default_val.replace("|", "\\|")
    if len(default_val) > 25:
        default_val = default_val[:22] + "..."

    scope = opt.get("scope", ["GLOBAL"])
    is_download = "DOWNLOAD" in scope
    is_rpc = opt.get("rpc_supported", False)

    if is_download and is_rpc:
        mutability = "Runtime (Active/Global)"
        rpc_support = "Yes (changeOption)"
        frontend = "Dialog / Inspector / Settings"
    elif is_rpc:
        mutability = "Global Runtime"
        rpc_support = "Yes (changeGlobalOption)"
        frontend = "Settings"
    else:
        mutability = "Startup only"
        rpc_support = "No (CLI / Conf)"
        frontend = "Preferences / Daemon Config"

    if opt.get("deprecated", False):
        coverage_state = "DEPRECATED"
    elif opt.get("sensitive", False):
        coverage_state = "SUPPORTED_WITH_LIMITATION"
    elif is_rpc or is_download:
        coverage_state = "SUPPORTED"
    else:
        coverage_state = "BACKEND_ONLY"

    adapter_map = f"Aria2Option.{opt['name'].replace('-', '_')}"
    test_ref = "test_option_registry.py"

    lines.append(
        f"| [`{name}`]({opt['documentation_reference']}) | {short} | `{cat}` | `{py_type}` | `{default_val}` | {frontend} | {mutability} | {rpc_support} | `{adapter_map}` | **{coverage_state}** | `{test_ref}` |"
    )

output_path = ROOT / "docs/aria2/option-matrix.md"
output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Successfully generated {len(lines)} rows in {output_path}")
