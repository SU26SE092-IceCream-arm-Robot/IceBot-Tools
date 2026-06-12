# Log Analyzer Usage

The log analyzer tails WebAPI and robot-style runtime logs, groups repeated errors, and reports simple runtime/design violations.

It is local tooling. It is not production monitoring and not the official IceBot runtime contract.

## Current Checks

- `SLOW_DATABASE_QUERY`: EF Core command elapsed time greater than `500ms`.
- `THREAD_BLOCKED`: robot control thread blocked longer than `1000ms`.
- repeated exception grouping by source, exception type, normalized message, and top stack frames.

## Generated Data

Generated data belongs outside source folders:

```text
data/log-analyzer/mock_logs/
logs/log-analyzer/violations.log
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

Short smoke test:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\generate_mock_logs.py --count 5
```

## Run Against Real Logs

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py `
  --webapi-path "D:\path\to\webapi\logs" `
  --robot-path "D:\path\to\robot\logs"
```

Override violation output:

```powershell
.\.venv\Scripts\python.exe .\log-analyzer\analyzer.py `
  --violations-log-path "D:\path\to\violations.log"
```

## Boundary

- Do not commit generated mock logs or violation logs.
- Do not store secrets or raw customer logs in this repository.
- Use this tool for local debugging, demo diagnostics, and future failure-memory experiments.
- For exact backend behavior, inspect source code and official backend docs.
