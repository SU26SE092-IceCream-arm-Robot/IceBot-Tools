# Docs Ops Usage

Docs Ops contains small documentation hygiene checks.

It does not rewrite documents, call an LLM, or run RAG ingest. It only reports issues.

## Commands

Run from `IceBot-Tools`.

```powershell
python .\docs-ops\commands\check_docs.py
```

Run individual checks only when debugging:

```powershell
python .\docs-ops\commands\check_links.py
python .\docs-ops\commands\check_doc_index.py
python .\docs-ops\commands\find_stale_refs.py
```

MCP also exposes one aggregate tool:

```text
check_icebot_docs
```

The MCP tool is quiet on success and structured on failure.

## Checks

| Command | Purpose |
| --- | --- |
| `check_docs.py` | Runs all docs hygiene checks in one command. |
| `check_links.py` | Scans Markdown files and reports local links pointing to missing files/folders. |
| `check_doc_index.py` | Verifies important index/router docs exist and their links resolve. |
| `find_stale_refs.py` | Finds references to known old paths such as deleted README files or moved docs. |

## Scope

Default scan root is the workspace root:

```text
IceCream_arm_Robot/
```

Ignored folders include:

```text
.git
.local
.venv
bin
obj
node_modules
data
logs
```

## When To Run

Run these checks after:

- moving docs;
- deleting README files;
- renaming folders;
- changing source-of-truth docs;
- updating RAG/context maps;
- cleaning Vault or project docs.

## Maintenance

`docs-ops/docsops/config.py` is the machine-readable rule file for this tool.

Update it when documentation structure changes in a way the checker should understand:

- add a new important index/router doc to `IMPORTANT_DOC_PATHS`;
- add a moved or deleted path to `STALE_REFERENCE_PATTERNS`;
- add a generated/local folder to `EXCLUDED_DIR_NAMES`;
- remove stale patterns after the project has fully migrated away from an old path.

Do not duplicate the full config list in Markdown. This page explains when to change the config; the Python config remains the executable source for the checker.

After changing the config, run:

```powershell
python .\docs-ops\commands\check_docs.py
```

## Boundary

- This is docs hygiene tooling, not documentation source of truth.
- Do not add semantic quality checks here yet.
- Do not auto-fix docs in V1.
- Keep stale-reference rules explicit in `docs-ops/docsops/config.py`.
- MCP output should stay quiet on success and verbose only on failure.
