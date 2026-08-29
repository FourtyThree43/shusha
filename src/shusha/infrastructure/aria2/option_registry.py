"""
Authoritative aria2 Option Registry and Serializer for Shusha 2.
Loads options directly from the verified specification catalogue.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from shusha.infrastructure.aria2.errors import Aria2OptionValidationError


@dataclass(frozen=True, slots=True)
class OptionDefinition:
    """Authoritative metadata for an aria2 command-line and RPC option."""

    name: str
    short_name: str | None
    category: str
    type: str
    default: str | None
    minimum: int | None
    maximum: int | None
    enum_values: list[str] | None
    scope: list[str]
    rpc_supported: bool
    cli_supported: bool
    sensitive: bool
    deprecated: bool
    experimental: bool
    description: str
    documentation_reference: str


class OptionRegistry:
    """Central registry and validator for all aria2 options."""

    _instance: OptionRegistry | None = None

    def __init__(self, options: list[OptionDefinition]) -> None:
        self._options: dict[str, OptionDefinition] = {opt.name: opt for opt in options}
        self._by_short: dict[str, OptionDefinition] = {
            opt.short_name: opt for opt in options if opt.short_name
        }

    @classmethod
    def load_from_spec(cls, spec_path: Path | None = None) -> Self:
        """Load the authoritative option registry from spec/aria2/options.json."""
        if spec_path is None:
            current = Path(__file__).resolve().parent
            while current != current.parent:
                candidate = current / "spec" / "aria2" / "options.json"
                if candidate.exists():
                    spec_path = candidate
                    break
                current = current.parent
            if spec_path is None:
                spec_path = (
                    Path(__file__).resolve().parents[4]
                    / "spec"
                    / "aria2"
                    / "options.json"
                )

        if not spec_path.exists():
            raise FileNotFoundError(
                f"Authoritative options specification not found at '{spec_path}'"
            )

        with open(spec_path, encoding="utf-8") as f:
            raw_options = json.load(f)

        definitions = [
            OptionDefinition(
                name=o["name"],
                short_name=o.get("short_name"),
                category=o["category"],
                type=o["type"],
                default=o.get("default"),
                minimum=o.get("minimum"),
                maximum=o.get("maximum"),
                enum_values=o.get("enum_values"),
                scope=o.get("scope", ["GLOBAL"]),
                rpc_supported=o.get("rpc_supported", True),
                cli_supported=o.get("cli_supported", True),
                sensitive=o.get("sensitive", False),
                deprecated=o.get("deprecated", False),
                experimental=o.get("experimental", False),
                description=o.get("description", ""),
                documentation_reference=o.get("documentation_reference", ""),
            )
            for o in raw_options
        ]
        return cls(definitions)

    @classmethod
    def get_default_registry(cls) -> OptionRegistry:
        """Singleton accessor for default registry."""
        if cls._instance is None:
            cls._instance = cls.load_from_spec()
        return cls._instance

    def get(self, name: str) -> OptionDefinition | None:
        """Look up an option by long name or short flag."""
        clean = name.lstrip("-")
        return self._options.get(clean) or self._by_short.get(clean)

    def contains(self, name: str) -> bool:
        return self.get(name) is not None

    def validate_option(self, name: str, value: str) -> tuple[bool, str | None]:
        """Validate an option value against its specification definition."""
        defn = self.get(name)
        if not defn:
            return False, f"Unknown aria2 option: '{name}'"

        val_str = str(value).strip()

        # Type validations
        if defn.type == "boolean":
            if val_str.lower() not in ("true", "false"):
                return (
                    False,
                    f"Option '{defn.name}' expects boolean ('true' or 'false'), got '{value}'",
                )

        elif (
            defn.type in ("integer", "duration", "size", "rate")
            and defn.minimum is not None
        ):
            if val_str.isdigit():
                num = int(val_str)
                if num < defn.minimum:
                    return (
                        False,
                        f"Option '{defn.name}' value {num} is below minimum {defn.minimum}",
                    )
                if defn.maximum is not None and num > defn.maximum:
                    return (
                        False,
                        f"Option '{defn.name}' value {num} exceeds maximum {defn.maximum}",
                    )

        elif (
            defn.type == "enum" and defn.enum_values and val_str not in defn.enum_values
        ):
            valid_choices = ", ".join(defn.enum_values)
            return (
                False,
                f"Option '{defn.name}' must be one of [{valid_choices}], got '{value}'",
            )

        return True, None

    def serialize_for_rpc(self, options: dict[str, str]) -> dict[str, str]:
        """Validate and prepare a dictionary of options for transmission over aria2 RPC."""
        validated: dict[str, str] = {}
        for k, v in options.items():
            clean_key = k.lstrip("-")
            is_valid, err_msg = self.validate_option(clean_key, v)
            if not is_valid:
                raise Aria2OptionValidationError(
                    err_msg or f"Invalid option: '{clean_key}'"
                )
            validated[clean_key] = str(v)
        return validated

    def serialize_for_cli(self, options: dict[str, str]) -> list[str]:
        """Serialize options to command-line argument array (e.g. ['--dir=/path'])."""
        args: list[str] = []
        for k, v in options.items():
            clean_key = k.lstrip("-")
            defn = self.get(clean_key)
            if defn and defn.type == "boolean" and str(v).lower() == "true":
                args.append(f"--{clean_key}")
            else:
                args.append(f"--{clean_key}={v}")
        return args

    def serialize_for_config_file(self, options: dict[str, str]) -> str:
        """Serialize options to aria2.conf configuration file format."""
        lines: list[str] = []
        for k, v in options.items():
            clean_key = k.lstrip("-")
            lines.append(f"{clean_key}={v}")
        return "\n".join(lines)

    def filter_by_category(self, category: str) -> list[OptionDefinition]:
        return [
            o for o in self._options.values() if o.category.lower() == category.lower()
        ]

    def filter_by_scope(self, scope: str) -> list[OptionDefinition]:
        return [o for o in self._options.values() if scope.upper() in o.scope]

    def search(self, query: str) -> list[OptionDefinition]:
        """Search options by name, category, or description."""
        q = query.strip().lower()
        if not q:
            return list(self._options.values())
        return [
            o
            for o in self._options.values()
            if q in o.name.lower()
            or q in o.category.lower()
            or q in o.description.lower()
        ]

    def is_sensitive(self, name: str) -> bool:
        defn = self.get(name)
        return defn.sensitive if defn else False
