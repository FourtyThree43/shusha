"""Batch URI and sequence pattern parser for Shusha-DM.

This module provides tools to extract, validate, and expand batch download URLs:
- Pattern range expansion: e.g. `http://site.com/ep[01-20].mp4` -> 20 individual URLs.
- Multi-line free-form text URL extraction.
- Automatic clipboard URL detection for magnet, torrent, http, and ftp links.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

URL_PATTERN = re.compile(
    r"(?:https?|ftp|sftp)://[^\s<>\"']+|magnet:\?[^\s<>\"']+",
    re.IGNORECASE,
)

RANGE_PATTERN = re.compile(r"\[(\d+)-(\d+)\]")
ALPHA_RANGE_PATTERN = re.compile(r"\[([a-zA-Z])-([a-zA-Z])\]")


def extract_urls(text: str) -> list[str]:
    """Extract all valid download URIs from raw text or multi-line strings.

    Args:
        text: Raw input text.

    Returns:
        List of cleaned unique URI strings in order of occurrence.
    """
    found: list[str] = []
    seen: set[str] = set()

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Look for range patterns first
        expanded = expand_pattern_url(line)
        if len(expanded) > 1:
            for url in expanded:
                if url not in seen:
                    seen.add(url)
                    found.append(url)
            continue

        # Match regular URLs or Magnet links
        matches = URL_PATTERN.findall(line)
        if matches:
            for m in matches:
                m_clean = m.strip()
                if m_clean not in seen:
                    seen.add(m_clean)
                    found.append(m_clean)
        elif (
            line.startswith("magnet:")
            or line.endswith(".torrent")
            or line.endswith(".metalink")
        ) and line not in seen:
            seen.add(line)
            found.append(line)

    return found


def expand_pattern_url(pattern_url: str) -> list[str]:
    """Expand range pattern brackets like `[01-10]` or `[a-z]` into a list of URLs.

    Args:
        pattern_url: URL string containing range brackets, e.g. `http://example.com/part[1-5].rar`.

    Returns:
        List of expanded URLs. If no pattern matches, returns `[pattern_url]`.
    """
    pattern_url = pattern_url.strip()

    # Numeric range check: [01-10]
    num_match = RANGE_PATTERN.search(pattern_url)
    if num_match:
        start_str, end_str = num_match.group(1), num_match.group(2)
        start, end = int(start_str), int(end_str)
        width = (
            len(start_str) if start_str.startswith("0") and len(start_str) > 1 else 0
        )

        step = 1 if end >= start else -1
        results: list[str] = []
        for i in range(start, end + step, step):
            formatted_num = f"{i:0{width}d}" if width > 0 else str(i)
            expanded = RANGE_PATTERN.sub(formatted_num, pattern_url, count=1)
            # Recursively expand any subsequent range brackets
            results.extend(expand_pattern_url(expanded))
        return results

    # Alpha range check: [a-f]
    alpha_match = ALPHA_RANGE_PATTERN.search(pattern_url)
    if alpha_match:
        start_char, end_char = alpha_match.group(1), alpha_match.group(2)
        start_code, end_code = ord(start_char), ord(end_char)
        step = 1 if end_code >= start_code else -1

        results = []
        for code in range(start_code, end_code + step, step):
            expanded = ALPHA_RANGE_PATTERN.sub(chr(code), pattern_url, count=1)
            results.extend(expand_pattern_url(expanded))
        return results

    return [pattern_url]


def is_downloadable_url(candidate: str) -> bool:
    """Validate whether candidate string looks like a supported download URI."""
    candidate = candidate.strip()
    if candidate.startswith("magnet:?xt="):
        return True
    try:
        parsed = urlparse(candidate)
        return parsed.scheme in ("http", "https", "ftp", "sftp") and bool(parsed.netloc)
    except Exception:
        return False
