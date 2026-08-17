"""Module for aria2c options.

This module defines the Options class, which holds information retrieved with the `get_option` or
`get_global_option` methods of the client.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from shusha.models.utilities import bool_or_value, bool_to_str

if TYPE_CHECKING:
    from shusha.controller.api import ShushaAPI as Api
    from shusha.models.structs_downloads import Download

OptionType = str | int | bool | float | None


class Options(Mapping[str, Any]):
    """Holds aria2 options with dynamic property and dictionary access.

    Options are accessible with snake_case (e.g. `options.max_download_limit`
    or `options.continue_downloads`), matching standard aria2 kebab-case options.
    """

    def __init__(
        self, api: Api, struct: dict[str, Any], download: Download | None = None
    ):
        self.__dict__["api"] = api
        self.__dict__["download"] = download
        self.__dict__["_struct"] = deepcopy(struct) if struct else {}

    def get(self, key: Any, default: Any = None, class_: Callable | None = None) -> Any:
        """Get an option value with optional type casting and default."""
        item = str(key)
        lookup_key = (
            "continue" if item == "continue_downloads" else item.replace("_", "-")
        )
        value = self._struct.get(lookup_key)
        if value is None:
            return default
        if class_ is bool or (
            isinstance(value, str) and value.lower() in ("true", "false")
        ):
            return bool_or_value(value)
        if class_ is not None:
            try:
                return class_(value)
            except (ValueError, TypeError):
                return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return bool_or_value(value)

    def set(self, item: str, value: OptionType) -> None:
        """Set an option value locally and on the aria2 daemon."""
        key = "continue" if item == "continue_downloads" else item.replace("_", "-")
        str_val = bool_to_str(value) if isinstance(value, bool) else str(value)
        self._struct[key] = str_val

        if self.api and hasattr(self.api, "client"):
            try:
                if self.download and self.download.gid:
                    self.api.client.change_option(self.download.gid, {key: str_val})
                else:
                    self.api.client.change_global_option({key: str_val})
            except Exception:
                pass

    def get_struct(self) -> dict[str, Any]:
        """Return the raw options dictionary."""
        return deepcopy(self._struct)

    def __getattr__(self, name: str) -> Any:
        if name in self.__dict__:
            return self.__dict__[name]
        key = "continue" if name == "continue_downloads" else name.replace("_", "-")
        if key in self._struct:
            return self.get(key)
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("api", "download", "_struct"):
            self.__dict__[name] = value
        else:
            self.set(name, value)

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None and key not in self._struct:
            raise KeyError(key)
        return val

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            k = "continue" if key == "continue_downloads" else key.replace("_", "-")
            return k in self._struct
        return False

    def __iter__(self) -> Iterator[str]:
        return iter(self._struct)

    def __len__(self) -> int:
        return len(self._struct)

    def __repr__(self) -> str:
        return f"Options({self._struct})"
