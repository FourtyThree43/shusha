# ADR-016: 132-Screen Feature Matrix Interpretation & Evolution

## Status
Accepted

## Context
The legacy Shusha repository defined a 132-screen catalogue covering aria2 functionality. As mandated by `AGENTS.md` RULE-020 and `PLAN.md`, this catalogue represents a feature-completeness acceptance baseline rather than a rigid 132-window hierarchy.

## Decision
1. Feature Completeness: Every feature in the 132-screen specification (options, peers, files, servers, piece maps, trackers, categories, batches, scheduler, proxy, checksums) is fully accessible across Desktop, TUI, and CLI surfaces.
2. Modern Information Architecture: Merge fragmented single-purpose dialogs into cohesive responsive workspaces:
   - Modern Navigation Rail with view switching (Dashboard, Transfers, Inbox, Media Grabber, Plugins, Doctor).
   - Unified Add Download Dialog with tabs for URL, Torrent/Magnet, Metalink, Batch patterns, and Media stream.
   - Live Inspector with multi-tab panels (Files, Peers, Pieces, Servers, Trackers, Options).

## Consequences
- **Positive**: 100% aria2 feature coverage preserved while delivering an intuitive, responsive user experience.
- **Positive**: Complies with both legacy feature baseline and modernized multi-backend architecture.
