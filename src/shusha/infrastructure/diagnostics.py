"""
Diagnostics bundle and system health report generator for Shusha 2.
Ensures zero secrets or credentials are ever exposed in diagnostic output.
"""

import platform
import sqlite3
import sys
from dataclasses import asdict
from importlib.metadata import version as get_pkg_version
from typing import Any

from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.daemon.discovery import (
    find_aria2_executable,
    inspect_aria2_version,
)
from shusha.infrastructure.daemon.health import probe_daemon_health
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.security.redaction import redact_dict_secrets


def generate_diagnostics_report(
    db_manager: DatabaseManager | None = None,
    settings_store: SettingsStore | None = None,
) -> dict[str, Any]:
    """Compile a comprehensive, sanitized diagnostic report for debugging and support."""
    try:
        shusha_ver = get_pkg_version("shusha")
    except Exception:
        shusha_ver = "2.0.0-dev"

    # 1. System & Environment
    system_info = {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "sqlite_version": sqlite3.sqlite_version,
    }

    # 2. aria2 Discovery & Inspection
    aria2_exe = find_aria2_executable()
    aria2_info: dict[str, Any] = {
        "executable_path": str(aria2_exe) if aria2_exe else None,
        "installed": aria2_exe is not None,
    }

    if aria2_exe:
        try:
            ver_str, features = inspect_aria2_version(aria2_exe)
            aria2_info["version"] = ver_str
            aria2_info["enabled_features"] = features
        except Exception as e:
            aria2_info["version_error"] = str(e)

    # 3. Settings & Storage
    settings_info: dict[str, Any] = {}
    if settings_store:
        try:
            settings_obj = settings_store.load_settings()
            raw_settings = asdict(settings_obj)
            settings_info = redact_dict_secrets(raw_settings)
        except Exception as e:
            settings_info["error"] = str(e)

    # 4. Daemon Health
    daemon_health_info: dict[str, Any] = {}
    host = settings_info.get("aria2_host", "127.0.0.1")
    port = int(settings_info.get("aria2_port", 6800))
    try:
        health_report = probe_daemon_health(host=host, port=port)
        daemon_health_info = {
            "status": health_report.status.value,
            "version": health_report.version,
            "latency_ms": health_report.latency_ms,
            "error": health_report.error_message,
        }
    except Exception as e:
        daemon_health_info["probe_error"] = str(e)

    report = {
        "shusha_version": shusha_ver,
        "system": system_info,
        "aria2": aria2_info,
        "settings": settings_info,
        "daemon_health": daemon_health_info,
    }

    # Ensure complete redaction
    return redact_dict_secrets(report)


def format_diagnostics_text(report: dict[str, Any]) -> str:
    """Format diagnostics dictionary into human-readable text."""
    lines = [
        "============================================================",
        f"  Shusha {report.get('shusha_version', '2.0')} System Diagnostics",
        "============================================================",
        "",
        "--- System Environment ---",
        f"  OS:              {report['system']['os']} {report['system']['release']} ({report['system']['machine']})",
        f"  Python:          {report['system']['python_version']} ({report['system']['python_implementation']})",
        f"  SQLite:          {report['system']['sqlite_version']}",
        "",
        "--- aria2c Engine ---",
        f"  Executable:      {report['aria2'].get('executable_path') or 'NOT FOUND'}",
        f"  Version:         {report['aria2'].get('version', 'N/A')}",
        f"  Features:        {', '.join(report['aria2'].get('enabled_features', [])) or 'N/A'}",
        "",
        "--- Daemon Health ---",
        f"  Status:          {report['daemon_health'].get('status', 'UNKNOWN')}",
        f"  Version:         {report['daemon_health'].get('version') or 'N/A'}",
        f"  Latency:         {report['daemon_health'].get('latency_ms', 'N/A')} ms",
    ]
    if report["daemon_health"].get("error"):
        lines.append(f"  Error:           {report['daemon_health']['error']}")

    lines.extend(
        [
            "",
            "--- Configuration ---",
        ]
    )
    for k, v in report.get("settings", {}).items():
        lines.append(f"  {k:24s}: {v}")

    lines.append("============================================================")
    return "\n".join(lines)
