import sys
import textwrap
from importlib import metadata
from pathlib import Path

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from platformdirs import user_config_dir, user_downloads_dir


def sizeof_fmt(num, delim=" ", suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{delim}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}{delim}Yi{suffix}"


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


# def save_configuration(config_dict):
#     """Save dict to TOML formatted string.

#     Args:
#         config_dict (dict): The dict configuration.
#     """
#     config_file = Path(user_config_dir("shusha")) / "config.toml"

#     new_config = config_dict.get("USER", {})

#     try:
#         config_file.parent.mkdir(parents=True, exist_ok=True)
#         with config_file.open("w") as fd:
#             fd.write(textwrap.dedent(new_config).lstrip("\n"))
#     except Exception as error:
#         print(f"Failed to save configuration file: {error}")

if __name__ == "__main__":
    print(get_version())

    config = load_configuration()
    print(config)
