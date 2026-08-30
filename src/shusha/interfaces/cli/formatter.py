"""
Output formatting module for Shusha CLI (Epic E13).
Supports human-readable tabular output, machine-readable JSON, and line-delimited JSONL streaming.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from shusha.acquisition.resolver import ResolutionResult
from shusha.domain.download import Download
from shusha.domain.job import Job
from shusha.domain.values import BitRate, ByteSize


class OutputFormat(StrEnum):
    """Supported CLI output serialization formats."""

    TABLE = "table"
    JSON = "json"
    JSONL = "jsonl"


def job_to_dict(item: Job | Download | dict[str, Any]) -> dict[str, Any]:
    """Convert a Job, Download, or dictionary into a normalized dictionary."""
    if isinstance(item, dict):
        return dict(item)

    if isinstance(item, Job):
        comp_bytes = item.progress.completed_length.bytes
        total_bytes = (
            item.progress.total_length.bytes
            if item.progress.total_length is not None
            else None
        )
        eta_sec = item.progress.eta.seconds if item.progress.eta is not None else None
        created_str = (
            item.timestamps.created_at.isoformat()
            if item.timestamps.created_at is not None
            else None
        )
        started_str = (
            item.timestamps.started_at.isoformat()
            if item.timestamps.started_at is not None
            else None
        )
        finished_str = (
            item.timestamps.finished_at.isoformat()
            if item.timestamps.finished_at is not None
            else None
        )
        source_uri = item.source.uri.raw_uri if item.source is not None else ""

        return {
            "id": str(item.id),
            "download_id": str(item.id),
            "name": item.name,
            "backend_id": str(item.backend_id),
            "state": item.state.value,
            "status": item.state.value.lower(),
            "group_id": str(item.group_id) if item.group_id is not None else None,
            "category": str(item.category_id or ""),
            "category_id": str(item.category_id)
            if item.category_id is not None
            else None,
            "source_uri": source_uri,
            "completed_bytes": comp_bytes,
            "total_bytes": total_bytes,
            "progress": item.progress.percentage.value,
            "download_speed": item.progress.download_speed.bytes_per_sec,
            "upload_speed": item.progress.upload_speed.bytes_per_sec,
            "eta_seconds": eta_sec,
            "error_message": item.error_message,
            "created_at": created_str,
            "started_at": started_str,
            "finished_at": finished_str,
            "metadata": item.metadata,
        }

    if isinstance(item, Download):
        comp_bytes = item.completed_length.bytes
        total_bytes = item.total_length.bytes if item.total_length is not None else None
        eta_sec = item.eta.seconds if item.eta is not None else None
        source_uri = item.sources[0].uri.raw_uri if item.sources else ""

        return {
            "id": str(item.download_id),
            "download_id": str(item.download_id),
            "gid": str(item.gid),
            "name": item.name,
            "backend_id": "aria2",
            "state": item.state.value,
            "status": item.state.value.lower(),
            "category": str(item.category_id or ""),
            "category_id": str(item.category_id)
            if item.category_id is not None
            else None,
            "source_uri": source_uri,
            "completed_bytes": comp_bytes,
            "total_bytes": total_bytes,
            "progress": item.progress.value,
            "download_speed": item.download_speed.bytes_per_sec,
            "upload_speed": item.upload_speed.bytes_per_sec,
            "eta_seconds": eta_sec,
            "connections": item.connections,
            "error_message": item.error_message,
        }

    return {"id": str(item)}


def resolution_to_dict(res: ResolutionResult) -> dict[str, Any]:
    """Convert ResolutionResult to dictionary."""
    return {
        "acquisition_id": str(res.acquisition_id),
        "original_input": res.original_input,
        "canonical_url": res.canonical_url,
        "detected_kind": res.resolved_kind.value,
        "candidate_backends": [str(b) for b in res.candidate_backends],
        "mirrors": list(res.mirrors),
        "metadata": dict(res.metadata),
        "is_resolved": res.is_resolved,
        "error": res.error,
    }


class CliFormatter:
    """Format domain entities and query/command outcomes for CLI presentation."""

    @staticmethod
    def format_jobs(
        items: Sequence[Job | Download | dict[str, Any]],
        output_format: OutputFormat,
    ) -> str:
        """Format a list of jobs/downloads into table, JSON, or JSONL."""
        data = [job_to_dict(j) for j in items]

        if output_format == OutputFormat.JSON:
            return json.dumps(data, indent=2)

        if output_format == OutputFormat.JSONL:
            return "\n".join(json.dumps(row) for row in data)

        # TABLE format
        if not data:
            return "No downloads found."

        header = f"{'ID':<16} {'NAME':<32} {'STATE':<12} {'PROGRESS':<10} {'SIZE':<22} {'SPEED':<12} {'BACKEND':<10} {'CATEGORY'}"
        lines = [header, "-" * len(header)]

        for d in data:
            jid = str(d.get("id") or d.get("download_id") or "")[:15]
            name = str(d.get("name") or "")[:30]
            state = str(d.get("state") or "")[:10]
            prog_val = d.get("progress")
            prog_str = (
                f"{prog_val:.1f}%" if isinstance(prog_val, (int, float)) else "0.0%"
            )

            comp = d.get("completed_bytes", 0) or 0
            tot = d.get("total_bytes")
            if tot is not None:
                size_str = f"{ByteSize(comp).human_readable()} / {ByteSize(tot).human_readable()}"
            else:
                size_str = ByteSize(comp).human_readable()

            speed_val = d.get("download_speed", 0) or 0
            speed_str = BitRate(speed_val).human_readable()

            bid = str(d.get("backend_id") or "-")[:9]
            cat = str(d.get("category") or d.get("category_id") or "-")

            lines.append(
                f"{jid:<16} {name:<32} {state:<12} {prog_str:<10} {size_str:<22} {speed_str:<12} {bid:<10} {cat}"
            )

        return "\n".join(lines)

    @staticmethod
    def format_job_detail(
        item: Job | Download | dict[str, Any],
        output_format: OutputFormat,
    ) -> str:
        """Format detailed information of a single job."""
        d = job_to_dict(item)

        if output_format == OutputFormat.JSON:
            return json.dumps(d, indent=2)

        if output_format == OutputFormat.JSONL:
            return json.dumps(d)

        # Key-value detail card
        comp = d.get("completed_bytes", 0) or 0
        tot = d.get("total_bytes")
        tot_str = (
            f"{ByteSize(tot).human_readable()} ({tot} bytes)"
            if tot is not None
            else "Unknown"
        )
        prog_val = d.get("progress")
        prog_str = f"{prog_val:.1f}%" if isinstance(prog_val, (int, float)) else "0.0%"
        dl_spd = BitRate(d.get("download_speed", 0) or 0).human_readable()
        ul_spd = BitRate(d.get("upload_speed", 0) or 0).human_readable()
        eta_val = d.get("eta_seconds")
        eta_str = f"{eta_val:.1f}s" if eta_val is not None else "-"

        lines = [
            f"Job ID:          {d.get('id') or d.get('download_id')}",
            f"Name:            {d.get('name')}",
            f"State:           {d.get('state')}",
            f"Backend:         {d.get('backend_id', '-')}",
            f"Category:        {d.get('category') or d.get('category_id') or '-'}",
            f"Source URI:      {d.get('source_uri') or '-'}",
            f"Progress:        {prog_str}",
            f"Completed Size:  {ByteSize(comp).human_readable()} ({comp} bytes)",
            f"Total Size:      {tot_str}",
            f"Download Speed:  {dl_spd}",
            f"Upload Speed:    {ul_spd}",
            f"ETA:             {eta_str}",
            f"Created At:      {d.get('created_at') or '-'}",
            f"Started At:      {d.get('started_at') or '-'}",
            f"Finished At:     {d.get('finished_at') or '-'}",
            f"Error Message:   {d.get('error_message') or 'None'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_action_results(
        results: Sequence[dict[str, Any]],
        output_format: OutputFormat,
        action_name: str = "Processed",
    ) -> str:
        """Format batch action outcomes (e.g. add, pause, resume, cancel, remove, retry)."""
        if output_format == OutputFormat.JSON:
            return json.dumps(list(results), indent=2)

        if output_format == OutputFormat.JSONL:
            return "\n".join(json.dumps(r) for r in results)

        lines: list[str] = []
        for r in results:
            jid = r.get("id") or r.get("download_id") or ""
            name = r.get("name")
            err = r.get("error")
            if err:
                lines.append(f"✖ Failed {action_name.lower()} {jid}: {err}")
            elif name:
                lines.append(f"✔ {action_name} download: {jid} ({name})")
            else:
                lines.append(f"✔ {action_name} download: {jid}")
        return "\n".join(lines)

    @staticmethod
    def format_resolution(
        res: ResolutionResult,
        output_format: OutputFormat,
    ) -> str:
        """Format acquisition resolution outcome."""
        data = resolution_to_dict(res)

        if output_format == OutputFormat.JSON:
            return json.dumps(data, indent=2)

        if output_format == OutputFormat.JSONL:
            return json.dumps(data)

        backends_str = (
            ", ".join(data["candidate_backends"])
            if data["candidate_backends"]
            else "None"
        )
        mirrors_str = ", ".join(data["mirrors"]) if data["mirrors"] else "None"

        lines = [
            f"Original Input:      {data['original_input']}",
            f"Canonical Target:    {data['canonical_url']}",
            f"Detected Kind:       {data['detected_kind']}",
            f"Candidate Backends:  {backends_str}",
            f"Mirrors:             {mirrors_str}",
            f"Resolved:            {data['is_resolved']}",
        ]
        if data["error"]:
            lines.append(f"Error:               {data['error']}")
        if data["metadata"]:
            lines.append("Metadata:")
            for k, v in data["metadata"].items():
                lines.append(f"  {k:18s}: {v}")

        return "\n".join(lines)

    @staticmethod
    def format_diagnostics(
        report: dict[str, Any],
        output_format: OutputFormat,
    ) -> str:
        """Format system diagnostics report."""
        if output_format == OutputFormat.JSON:
            return json.dumps(report, indent=2)

        if output_format == OutputFormat.JSONL:
            return json.dumps(report)

        from shusha.infrastructure.diagnostics import format_diagnostics_text

        return format_diagnostics_text(report)

    @staticmethod
    def format_error(
        message: str,
        output_format: OutputFormat,
    ) -> str:
        """Format an error message according to selected format."""
        if output_format in (OutputFormat.JSON, OutputFormat.JSONL):
            payload = {"error": message, "status": "failed"}
            return json.dumps(
                payload, indent=2 if output_format == OutputFormat.JSON else None
            )

        return f"✖ Error: {message}"
