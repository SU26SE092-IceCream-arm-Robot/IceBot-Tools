# Docs Ops Usage

Docs Ops contains small documentation hygiene checks.

It does not rewrite documents, call an LLM, or run RAG ingest. It only reports issues.

## Commands

Run from `IceBot-Tools`.

```powershell
python .\docs-ops\commands\check_docs.py
```

Check that REST and GraphQL authorization policies are present in the backend
permission matrix:

```powershell
python .\docs-ops\commands\check_api_inventory.py
```

Export the executable REST inventory from controller attributes for a review
or documentation update. The output is generated evidence, not a maintained
source document:

```powershell
python .\docs-ops\commands\export_rest_route_inventory.py `
  --output .\artifacts\rest-route-inventory.md
```

Export a stable JSON catalog for cross-repository implementation contracts.
The output is generated evidence; regenerate it after controller-route changes:

```powershell
python .\docs-ops\commands\export_rest_operation_catalog.py `
  --output ..\IceBot-Product\delivery\catalogs\OPERATION_CATALOG.json
```

Prepare a focused contract packet for an AI or contributor. It navigates the
correct documents and evidence targets; it does not claim the target repository
is complete:

```powershell
python .\docs-ops\commands\prepare_implementation_packet.py `
  --target IceBot-Kiosk `
  --id FLOW-CHECKOUT-EXECUTION
```

Create an evidence checklist for the current WebApp source. The result is not
a semantic completion claim; give it to an AI/reviewer with the linked flow
contracts:

```powershell
python .\docs-ops\commands\audit_target_capability_evidence.py `
  --target IceBot-WebApp `
  --output ..\IceBot-WebApp\.project-memory\capability-evidence.md
```

Show confirmed contract changes the WebApp has not acknowledged yet:

```powershell
python .\docs-ops\commands\prepare_contract_change_packet.py `
  --target IceBot-WebApp
```

In Product-repository CI, require a change-ledger update when contract-owning
files change. Supply the PR merge-base or target branch ref:

```powershell
python .\docs-ops\commands\check_contract_change_coverage.py `
  --base origin/main
```

Verify the cross-repository flow, capability, message, and generated REST
catalog links before handing contracts to another repository:

```powershell
python .\docs-ops\commands\check_implementation_contracts.py
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
| `check_links.py` | Scans Markdown files and reports missing local files/folders and invalid Markdown heading anchors. |
| `check_doc_index.py` | Verifies important index/router docs exist and their links resolve. |
| `find_stale_refs.py` | Finds references to known old paths such as deleted README files or moved docs. |
| `check_api_inventory.py` | Verifies policy alignment across REST/GraphQL usage, ASP.NET registration, and `PermissionMatrixRules`. |
| `export_rest_route_inventory.py` | Exports controller-attribute REST routes as reviewable Markdown. |
| `export_rest_operation_catalog.py` | Exports stable REST operation IDs and route/policy evidence as JSON. |
| `prepare_implementation_packet.py` | Produces focused reading/evidence instructions for a target role or repository. |
| `audit_target_capability_evidence.py` | Produces candidate path evidence for a frontend capability audit. |
| `prepare_contract_change_packet.py` | Produces confirmed target-specific contract changes after acknowledgement. |
| `check_contract_change_coverage.py` | Requires Product impact-ledger review when contract-owning files change. |
| `check_implementation_contracts.py` | Validates flow/capability/message links and generated REST catalog freshness. |

The aggregate check also validates `IceBot-Backend/docs` structure: active documents must stay at or below 500 lines, individual level-two/level-three sections must stay at or below 120 lines, non-README documents need `Search Keywords` and `Related Docs`, historical/deprecated/proposal files must live in Vault rather than the active backend source-of-truth tree, and authorization policies stay aligned across endpoint usage, ASP.NET registration, and the permission matrix.

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
- Keep checks structural and deterministic; semantic contract review remains a human/code-review responsibility.
- Do not auto-fix docs in V1.
- Keep stale-reference rules explicit in `docs-ops/docsops/config.py`.
- MCP output should stay quiet on success and verbose only on failure.
