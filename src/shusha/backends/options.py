"""Backend Option Specification and Validation Model (E05-I04)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from shusha.backends.errors import BackendOptionValidationError


class OptionType(StrEnum):
    """Data types for backend configuration options."""

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CHOICE = "choice"
    LIST = "list"
    PATH = "path"


class OptionScope(StrEnum):
    """Applicability scope of a configuration option."""

    GLOBAL = "global"
    JOB = "job"
    BOTH = "both"


class OptionMutability(StrEnum):
    """Runtime mutability behavior of an option."""

    STATIC = "static"  # Only settable before job start or daemon launch
    DYNAMIC = "dynamic"  # Modifiable while job is running via changeOption


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendOptionSpec:
    """Typed metadata and validation specification for backend-specific options."""

    name: str
    short_name: str | None = None
    option_type: OptionType = OptionType.STRING
    default_value: Any = None
    allowed_values: tuple[str, ...] | None = None
    scope: OptionScope = OptionScope.BOTH
    mutability: OptionMutability = OptionMutability.DYNAMIC
    description: str = ""
    security_sensitive: bool = False

    def validate(self, val: Any) -> str:
        """Validate and normalize an option value into a serializable string representation."""
        if val is None:
            return ""

        if self.option_type == OptionType.BOOL:
            if isinstance(val, bool):
                return "true" if val else "false"
            str_val = str(val).strip().lower()
            if str_val in ("true", "1", "yes", "on"):
                return "true"
            if str_val in ("false", "0", "no", "off"):
                return "false"
            raise BackendOptionValidationError(
                self.name, str(val), "Must be a valid boolean value"
            )

        if self.option_type == OptionType.INT:
            try:
                int_val = int(val)
                return str(int_val)
            except (ValueError, TypeError) as err:
                raise BackendOptionValidationError(
                    self.name, str(val), "Must be an integer"
                ) from err

        if self.option_type == OptionType.FLOAT:
            try:
                flt_val = float(val)
                return str(flt_val)
            except (ValueError, TypeError) as err:
                raise BackendOptionValidationError(
                    self.name, str(val), "Must be a numeric float"
                ) from err

        if self.option_type == OptionType.CHOICE:
            str_val = str(val).strip()
            if self.allowed_values and str_val not in self.allowed_values:
                allowed_str = ", ".join(self.allowed_values)
                raise BackendOptionValidationError(
                    self.name,
                    str_val,
                    f"Must be one of allowed values: [{allowed_str}]",
                )
            return str_val

        return str(val)
