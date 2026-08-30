"""aria2 option catalogue loader and typed BackendOptionSpec binding (E07-I07)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from shusha.backends.options import (
    BackendOptionSpec,
    OptionMutability,
    OptionScope,
    OptionType,
)


def _map_type(type_str: str) -> OptionType:
    mapping = {
        "string": OptionType.STRING,
        "integer": OptionType.INT,
        "float": OptionType.FLOAT,
        "boolean": OptionType.BOOL,
        "enum": OptionType.CHOICE,
        "choice": OptionType.CHOICE,
        "list": OptionType.LIST,
        "path": OptionType.PATH,
    }
    return mapping.get(type_str.lower(), OptionType.STRING)


def _map_scope(scopes: list[str]) -> OptionScope:
    has_global = "GLOBAL" in scopes
    has_job = any(s in ("DOWNLOAD", "JOB") for s in scopes)
    if has_global and has_job:
        return OptionScope.BOTH
    if has_job:
        return OptionScope.JOB
    return OptionScope.GLOBAL


@lru_cache(maxsize=1)
def load_aria2_options() -> list[BackendOptionSpec]:
    """Load authoritative 198 aria2 options from spec/aria2/options.json."""
    spec_path = Path(__file__).parents[4] / "spec" / "aria2" / "options.json"
    if not spec_path.exists():
        # Fallback search
        alt_path = Path("spec/aria2/options.json")
        if alt_path.exists():
            spec_path = alt_path
        else:
            return []

    try:
        data = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    specs: list[BackendOptionSpec] = []
    for item in data:
        name = item.get("name", "")
        if not name:
            continue

        specs.append(
            BackendOptionSpec(
                name=name,
                short_name=item.get("short_name"),
                option_type=_map_type(item.get("type", "string")),
                default_value=item.get("default"),
                allowed_values=tuple(item.get("enum_values"))
                if item.get("enum_values")
                else None,
                scope=_map_scope(item.get("scope", ["GLOBAL"])),
                mutability=OptionMutability.DYNAMIC
                if item.get("rpc_supported")
                else OptionMutability.STATIC,
                description=item.get("description", ""),
                security_sensitive=bool(item.get("sensitive", False)),
            )
        )
    return specs
