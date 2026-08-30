# ADR-003: Granular Capability Model for Dynamic Backend Selection

## Status
Accepted

## Context
Different execution engines have distinct capabilities (e.g., `aria2c` excels at multi-source segmentation and BitTorrent; `yt-dlp` excels at media stream extraction, quality resolution, and subtitle downloading). Assuming all backends support all features leads to runtime errors and architectural coupling.

## Decision
1. Define `Capability` as a typed `StrEnum` (e.g., `HTTP`, `HTTPS`, `BITTORRENT`, `METALINK`, `PAUSE_RESUME`, `BANDWIDTH_LIMIT`, `MEDIA_EXTRACTION`, `FORMAT_SELECTION`, `SUBTITLES`, `POST_PROCESSING`).
2. Backends declare an immutable `CapabilitySet`.
3. The routing policy engine matches the requirements of an `AcquisitionRequest` against available backends.

## Consequences
- **Positive**: Frontends dynamically enable/disable UI controls (e.g., peer inspector, subtitle selector) based on backend capabilities.
- **Positive**: Prevents impossible command dispatching (e.g., requesting peer lists on a yt-dlp job).
