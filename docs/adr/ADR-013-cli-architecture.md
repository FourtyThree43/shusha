# ADR-013: Unified CLI Dispatcher with Structured JSON/JSONL Output

## Status
Accepted

## Context
Scripting, CI pipelines, and automation tools require programmatic command execution (add, list, pause, resume, cancel, remove, status, resolve, doctor) with machine-readable, stable outputs.

## Decision
1. Modular CLI parser (`src/shusha/interfaces/cli/parser.py`) routes all subcommands through `CommandBus` and `QueryBus` (`src/shusha/interfaces/cli/dispatcher.py`).
2. Output Formatter (`src/shusha/interfaces/cli/formatter.py`) supports:
   - `table`: Human-friendly formatted tables.
   - `json` / `--json`: Formatted JSON objects with standard exit codes.
   - `jsonl` / `--jsonl`: Line-delimited JSON streams for live event piping.
3. Invocation defaults:
   - `shusha` (bare) -> Textual TUI.
   - `shusha --gui` or `shusha gui` -> Desktop GUI.
   - `shusha [cmd]` -> Direct CLI execution.

## Consequences
- **Positive**: Complete automation support with stable JSON schemas.
- **Positive**: Strict decoupling: CLI commands never interact directly with concrete backend daemons.
