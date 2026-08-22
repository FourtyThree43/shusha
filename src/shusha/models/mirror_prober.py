"""Multi-mirror latency and speed prober for download acceleration.

Tests multiple mirror URLs in parallel to evaluate:
- Time To First Byte (TTFB) / ping latency.
- HTTP Range support (Accept-Ranges: bytes).
- Content-Length verification across mirrors.
- Server responsiveness ranking.
"""

from __future__ import annotations

import concurrent.futures
import time
from dataclasses import dataclass
from urllib import request
from urllib.parse import urlparse

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


@dataclass
class MirrorProbeResult:
    """Result of probing a download mirror URL."""

    url: str
    is_alive: bool
    latency_ms: float
    supports_ranges: bool
    content_length: int | None
    status_code: int
    error: str | None = None

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc or self.url


class MirrorProber:
    """Probes and benchmarks multiple mirror sources concurrently."""

    @classmethod
    def probe_single_mirror(cls, url: str, timeout: float = 3.0) -> MirrorProbeResult:
        """Probe a single mirror URL with an HTTP HEAD request.

        Args:
            url: Target mirror URL.
            timeout: Timeout in seconds.

        Returns:
            MirrorProbeResult with latency and range capabilities.
        """
        start_time = time.perf_counter()
        req = request.Request(
            url,
            headers={"User-Agent": "Shusha-DM/MirrorProber", "Range": "bytes=0-0"},
            method="HEAD",
        )
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                status = resp.status
                accept_ranges = resp.headers.get("Accept-Ranges", "").lower() == "bytes"
                content_range = "Content-Range" in resp.headers
                supports_ranges = accept_ranges or content_range or status == 206

                clen_header = resp.headers.get("Content-Length")
                content_length = int(clen_header) if clen_header and clen_header.isdigit() else None

                return MirrorProbeResult(
                    url=url,
                    is_alive=True,
                    latency_ms=round(elapsed_ms, 2),
                    supports_ranges=supports_ranges,
                    content_length=content_length,
                    status_code=status,
                )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return MirrorProbeResult(
                url=url,
                is_alive=False,
                latency_ms=round(elapsed_ms, 2),
                supports_ranges=False,
                content_length=None,
                status_code=getattr(e, "code", 0) if hasattr(e, "code") else 0,
                error=str(e),
            )

    @classmethod
    def probe_mirrors(
        cls,
        urls: list[str],
        max_workers: int = 8,
        timeout: float = 3.0,
    ) -> list[MirrorProbeResult]:
        """Probe multiple mirror URLs concurrently and sort by fastest latency.

        Args:
            urls: List of mirror URL strings.
            max_workers: Thread pool size.
            timeout: Timeout per mirror.

        Returns:
            List of MirrorProbeResult sorted with responsive, lowest-latency mirrors first.
        """
        results: list[MirrorProbeResult] = []
        if not urls:
            return results

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls), max_workers)) as executor:
            future_to_url = {
                executor.submit(cls.probe_single_mirror, u, timeout): u for u in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    u = future_to_url[future]
                    results.append(
                        MirrorProbeResult(
                            url=u,
                            is_alive=False,
                            latency_ms=9999.0,
                            supports_ranges=False,
                            content_length=None,
                            status_code=0,
                            error=str(exc),
                        )
                    )

        # Sort: alive mirrors first, then ascending by latency
        results.sort(key=lambda r: (not r.is_alive, r.latency_ms))
        return results
