# ADR-008: yt-dlp Backend Integration Strategy & Stream Inspector

## Status
Accepted

## Context
Downloading media streams from platforms like YouTube, Vimeo, Twitch, and SoundCloud requires specialized extractor logic and dynamic format negotiation. Core must not be polluted with yt-dlp specific command-line arguments or format strings.

## Decision
1. Implement `YtDlpBackend(BackendProtocol)` in `src/shusha/backends/ytdlp/`.
2. Safe subprocess execution: Execute `yt-dlp` using argument arrays (never shell string concatenation).
3. Non-destructive stream inspection: `MediaInspector` uses `--dump-json` to extract `MediaMetadata` and `MediaFormat` (resolution, fps, vcodec, acodec, filesize) without initiating downloads.
4. Clean separation: Format selection and quality preferences are resolved in the application layer and passed as typed options.

## Consequences
- **Positive**: Full streaming site compatibility with zero shell injection risk.
- **Positive**: Enables rich format-picking UI in both Desktop and Terminal TUI.
