# ADR-002: Converged Acquisition Pipeline & Request Lifecycle

## Status
Accepted

## Context
Downloads originate from diverse sources (clipboard polling, browser extensions, drag-and-drop, torrent/metalink files, manual URL entries, and CLI arguments). Directly creating downloads from raw inputs bypasses format validation, mirror discovery, and backend matching.

## Decision
All acquisition inputs converge into a typed `AcquisitionRequest`. The pipeline processes items in 5 distinct, decoupled stages:
1. **Detection**: `AcquisitionDetector` classifies inputs into `DetectedKind` (DIRECT_URL, MAGNET, TORRENT_FILE, METALINK, MEDIA_STREAM, BATCH_RANGE, RAW_TEXT).
2. **Inspection**: `AcquisitionInspector` runs non-destructive probes (HTTP HEAD headers, torrent infohashes, MIME types) without initiating full transfers.
3. **Resolution**: `AcquisitionResolver` unpacks redirects, mirror candidates, and media metadata.
4. **Policy Routing**: `AcquisitionPolicyEngine` evaluates rules and capability requirements to recommend optimal execution backends (`aria2`, `yt-dlp`).
5. **Inbox & Staging**: `AcquisitionInbox` tracks lifecycle states (`detected`, `inspecting`, `resolved`, `awaiting_user`, `accepted`, `ignored`, `expired`, `failed`).

## Consequences
- **Positive**: Uniform security sanitization and deduplication across all entry sources.
- **Positive**: Clean separation between inspecting incoming URLs and executing heavy downloads.
