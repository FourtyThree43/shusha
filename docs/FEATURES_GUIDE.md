# Shusha Features & Capabilities Guide

This guide provides a comprehensive overview of all capabilities implemented in **Shusha Download Manager**.

---

## 1. Bitfield Piece Map Visualizer

Shusha includes a real-time 2D piece map visualizer modeled after BitTorrent desktop clients:
- **Bitfield Decoding**: Automatically converts aria2 hex-encoded bitfields into binary block arrays.
- **Canvas Rendering**: Renders blocks color-coded according to state:
  - 🟩 Completed & Hash-Verified Piece
  - ⬛ Pending Piece
- **Responsive Layout**: Dynamically reflows chunk grid columns on window resize.

---

## 2. Public BitTorrent Tracker Aggregator

Inspired by **Motrix**, Shusha auto-syncs with top-performing public BitTorrent trackers:
- **Automated Discovery**: Fetches from curated tracker repositories (e.g. `trackers_best.txt`).
- **Dynamic Tier Injection**: Injects tracker announce tiers directly into active torrents via `aria2.changeOption(gid, {"bt-tracker": "..."})`.
- **Peer Discovery Boost**: Drastically improves swarm discovery and speeds for rare magnet links.

---

## 3. Smart Batch Link Parser & Sequence Ranges

Shusha allows users to download large media series or split archives with minimal typing:
- **Numeric Ranges**: `https://example.com/part[01-20].rar` expands to 20 individual tasks.
- **Alphabetic Ranges**: `https://example.com/slide_[a-e].png` expands to 5 download tasks.
- **Clipboard Watcher**: Auto-detects URLs and magnet links from your clipboard.
- **Custom Per-Batch Options**: Specify custom Referer, User-Agent, and chunk splits per batch.

---

## 4. Bandwidth Scheduler & Speed Throttling

Automate your download bandwidth according to your daily schedule:
- **Time-Window Rules**: Set download and upload caps for specific times of day (e.g., limit to 1 MB/s during work hours, uncapped at night).
- **Per-Download Limiting**: Set discrete limits on individual downloads in the Inspector window.

---

## 5. Live Bandwidth Sparkline & Speed Graph

Track network performance with a real-time 60-second historical chart:
- **Download Rate (Green)**: Live throughput graph.
- **Upload Rate (Blue)**: Live upload rate for seeding torrents.
- **Peak Tracking**: Instant identification of speed peaks and bottlenecks.
