"""
This module contains utility functions that are used to perform common tasks by
other modules in the `shusha` package.
"""

import textwrap
from datetime import timedelta
from importlib import metadata
from pathlib import Path
from typing import Any

try:
    import tomllib  # ty: ignore[unresolved-import]
except ModuleNotFoundError:
    import tomli as tomllib  # ty: ignore[unresolved-import]

from platformdirs import (
    user_cache_dir,
    user_config_dir,
    user_data_dir,
    user_downloads_dir,
    user_log_dir,
)


def download_dir() -> Path:
    """Return the default download directory.

    Returns:
        The default download directory.
    """
    return Path(user_downloads_dir())


def config_dir(appname: str) -> Path:
    """Return the default user configuration directory.

    Args:
        appname (str): The name of the application.

    Returns:
        The default user configuration directory.
    """
    return Path(user_config_dir(appname))


def data_dir(appname: str) -> Path:
    """Return the default user data directory.

    Args:
        appname (str): The name of the application.

    Returns:
        The default user data directory.
    """
    return Path(user_data_dir(appname))


def cache_dir(appname: str) -> Path:
    """Return the default user cache directory.

    Args:
        appname (str): The name of the application.

    Returns:
        The default user cache directory.
    """
    return Path(user_cache_dir(appname))


def log_dir(appname: str) -> Path:
    """Return the default user log directory.

    Args:
        appname (str): The name of the application.

    Returns:
        The default user log directory.
    """
    return Path(user_log_dir(appname))


def bool_or_value(value: Any) -> Any:
    """
    Return `True` for `"true"`, `False` for `"false"`, original value otherwise.

    Parameters:
        value: Any kind of value.

    Returns:
        One of these values:
            - `True` for `"true"`
            - `False` for `"false"`
            - Original value otherwise
    """
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def bool_to_str(value: Any) -> Any:
    """
    Return `"true"` for `True`, `"false"` for `False`, original value otherwise.

    Parameters:
        value: Any kind of value.

    Returns:
        - `"true"` for `True`
        - `"false"` for `False`
        - Original value otherwise
    """
    if value is True:
        return "true"
    if value is False:
        return "false"
    return value


def sizeof_fmt(num: float, delim: str = " ", suffix: str = "B") -> str:
    """Convert a number of bytes into a human readable format.

    Args:
        num (int): The number of bytes.
        delim (str, optional): The delimiter. Defaults to " ".
        suffix (str, optional): The suffix. Defaults to "B".

    Returns:
        str: The human readable format.
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.2f}{delim}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f}{delim}Yi{suffix}"


def format_speed(speed: float):
    """Format a number of bytes into a human readable format.

    Args:
        speed (int): The number of bytes.

    Returns:
        str: The human readable format.
    """
    return sizeof_fmt(speed, suffix="B/s")


def format_size(size: float):
    """Format a number of bytes into a human readable format.

    Args:
        size (int): The number of bytes.

    Returns:
        str: The human readable format.
    """
    return sizeof_fmt(size, suffix="B")


def timedelta_fmt(value: timedelta, precision: int = 0) -> str:
    """
    Format a timedelta into a human readable format.

    Args:
        value (timedelta): The timedelta.
        precision (int, optional): The precision. Defaults to 0.

            - `0` to display all units
            - `1` to display the biggest unit only
            - `2` to display the first two biggest units only
            - `n` for the first N biggest units, etc.

    Returns:
        str: The human readable format.
    """
    pieces = []

    def add_piece(unit: int, label: str):
        """
        Add a formatted piece to the pieces list.
        """
        if unit > 0:
            piece_fmt = f"{unit}{label}" if unit > 1 else f"{unit}{label[:-1]}"
            pieces.append(piece_fmt)

    add_piece(value.days, "D:")

    hours, seconds = divmod(value.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    add_piece(hours, "H:")
    add_piece(minutes, "M:")
    add_piece(seconds, "S")

    return "".join(pieces[:precision] if precision > 0 else pieces)


def format_eta(eta: timedelta, precision: int = 0) -> str:
    """Format a number of seconds into a human readable format.

    Args:
        eta (int): The number of seconds.
        precision (int, optional): The precision. Defaults to 0.

            - `0` to display all units
            - `1` to display the biggest unit only
            - `2` to display the first two biggest units only
            - `n` for the first N biggest units, etc.

    Returns:
        str: The human readable format.
    """
    if eta == timedelta.max:
        return "-"
    return timedelta_fmt(eta, precision=precision)


def get_version() -> str:
    """Return the current `shusha` version.

    Returns:
        The current `shusha` version.
    """
    try:
        return metadata.version("shusha")
    except metadata.PackageNotFoundError:
        return "0.0.0"


def load_configuration():
    """Return dict from TOML formatted string or file.

    Returns:
        The dict configuration.
    """
    default_config = f"""
    [aria2]
    host = "localhost"
    port = 6800
    secret = "*******"
    timeout = 60
    max_retries = 5
    retry_wait = 2

    [aria2.options]
    dir = "{Path(user_downloads_dir()).as_posix()}"
    max_concurrent_downloads = 5
    max_connection_per_server = 5
    split = 8
    continue = true
    input_file = ""
    save_session = ""
    save_session_interval = 20

    [aria2.options.http]
    accept_gzip = true
    all_proxy = ""
    all_proxy_passwd = ""
    all_proxy_user = ""
    """
    config_dict = {}
    config_dict["DEFAULT"] = tomllib.loads(default_config)

    # Check for configuration file
    config_file = Path(user_config_dir("shusha")) / "config.toml"

    if config_file.exists():
        try:
            with config_file.open("rb") as config_file:
                config_dict["USER"] = tomllib.load(config_file)
        except Exception as error:
            print(f"Failed to load configuration file: {error}")
    else:
        # Write initial configuration file if it does not exist
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with config_file.open("w") as fd:
            fd.write(textwrap.dedent(default_config).lstrip("\n"))

    return config_dict


def dump_toml(data: dict) -> str:
    """Format dictionary into standard TOML string representation."""
    lines: list[str] = []
    for section, values in data.items():
        if isinstance(values, dict):
            lines.append(f"[{section}]")
            for k, v in values.items():
                if isinstance(v, bool):
                    lines.append(f"{k} = {'true' if v else 'false'}")
                elif isinstance(v, (int, float)):
                    lines.append(f"{k} = {v}")
                else:
                    lines.append(f'{k} = "{v}"')
            lines.append("")
        else:
            if isinstance(values, bool):
                lines.append(f"{section} = {'true' if values else 'false'}")
            elif isinstance(values, (int, float)):
                lines.append(f"{section} = {values}")
            else:
                lines.append(f'{section} = "{values}"')
    return "\n".join(lines)


def save_configuration(
    config_dict: dict, config_path: str | Path | None = None
) -> bool:
    """Save dict configuration to TOML formatted file.

    Args:
        config_dict: The dict configuration.
        config_path: Optional explicit configuration file path.

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    if config_path is None:
        config_file = Path(user_config_dir("shusha")) / "config.toml"
    else:
        config_file = Path(config_path)

    new_config = config_dict.get("USER", config_dict)

    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        toml_content = (
            dump_toml(new_config) if isinstance(new_config, dict) else str(new_config)
        )
        with config_file.open("w", encoding="utf-8") as fd:
            fd.write(toml_content)
        return True
    except Exception as error:
        print(f"Failed to save configuration file: {error}")
        return False


if __name__ == "__main__":
    print(get_version())

    config = load_configuration()
    print(config)
