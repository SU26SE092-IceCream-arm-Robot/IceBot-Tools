# Log Analyzer

The log analyzer tails WebAPI and robot runtime log files, groups repeated errors, and reports simple design/runtime violations.

This is local tooling. It is not a production monitoring system and it is not the official IceBot runtime contract.

## What It Watches

- WebAPI logs in JSON/Serilog-style line format.
- Robot logs in text format:

```text
[2026-06-11 22:52:00] [ERROR] RobotController: Failed to execute command.
```

Plain-text WebAPI fallback is intentionally minimal in V1. Prefer structured WebAPI logs when using this tool.

## Current Checks

- `SLOW_DATABASE_QUERY`: EF Core database command elapsed time greater than `500ms`.
- `THREAD_BLOCKED`: robot control thread blocked longer than `1000ms`.
- repeated exception grouping by source, exception type, normalized message, and top stack frames.

## Generated Data

Generated data is kept outside the source folder:

```text
IceBot-Tools/data/log-analyzer/mock_logs/
IceBot-Tools/logs/log-analyzer/violations.log
```

Both locations are ignored by git.

## Run With Mock Logs

From `IceBot-Tools`:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py
```

In a second terminal:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\generate_mock_logs.py
```

For a short smoke test that exits automatically:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\generate_mock_logs.py --count 5
```

The analyzer defaults to:

```text
data/log-analyzer/mock_logs/webapi
data/log-analyzer/mock_logs/robot
```

## Run Against Real Logs

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py `
  --webapi-path "D:\path\to\webapi\logs" `
  --robot-path "D:\path\to\robot\logs"
```

Override the violations output path if needed:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py `
  --violations-log-path "D:\path\to\violations.log"
```

## Boundary

- Do not commit generated mock logs or violation logs.
- Do not store secrets or raw customer logs in this repository.
- Use this tool for local debugging, demo diagnostics, and future failure-memory experiments.
- For exact backend behavior, inspect source code and official backend docs.
