from __future__ import annotations

import json
from pathlib import Path

import yaml

from docsops.api_inventory import extract_rest_endpoints, render_operation_catalog
from toolcore.workspace import WORKSPACE_ROOT


PRODUCT_ROOT = WORKSPACE_ROOT / "IceBot-Product"
DELIVERY_ROOT = PRODUCT_ROOT / "delivery"
VALID_CAPABILITY_STATUSES = {
    "complete",
    "partial",
    "missing",
    "contradictory",
    "blocked-by-backend",
    "not-applicable",
    "unverified",
}


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _resolved(base: Path, target: str) -> Path:
    return (base / target).resolve()


def check_implementation_contracts(*, max_failures: int = 30) -> dict:
    failures: list[dict] = []
    catalog_path = DELIVERY_ROOT / "catalogs" / "FLOW_CATALOG.yaml"
    catalog = _load_yaml(catalog_path)
    flow_ids: set[str] = set()
    capabilities_by_target: dict[str, set[str]] = {}
    for flow in catalog.get("flows", []):
        flow_id = flow.get("id")
        if not flow_id or flow_id in flow_ids:
            failures.append({"file": str(catalog_path), "target": str(flow_id), "reason": "missing or duplicate flow id"})
            continue
        flow_ids.add(flow_id)
        for key in ("backend_flow", "product_journey"):
            target = flow.get(key)
            if not target or not _resolved(catalog_path.parent, target).is_file():
                failures.append({"file": str(catalog_path), "target": str(target), "reason": f"missing {key} target"})

    for manifest_path in sorted((DELIVERY_ROOT / "targets").rglob("CONTRACT.yaml")):
        manifest = _load_yaml(manifest_path)
        target = manifest.get("target", {})
        target_id = target.get("id")
        for flow_id in target.get("related_flows", []):
            if flow_id not in flow_ids:
                failures.append({"file": str(manifest_path), "target": str(flow_id), "reason": "target references unknown related flow"})
        if target.get("kind") != "frontend":
            continue
        capability_ids: set[str] = set()
        for capability in manifest.get("capabilities", []):
            capability_id = capability.get("id")
            if not capability_id or capability_id in capability_ids:
                failures.append({"file": str(manifest_path), "target": str(capability_id), "reason": "missing or duplicate capability id"})
                continue
            capability_ids.add(capability_id)
            if capability.get("flow") not in flow_ids:
                failures.append({"file": str(manifest_path), "target": str(capability.get("flow")), "reason": "capability references unknown flow"})
        assigned = {
            item
            for flow in catalog.get("flows", [])
            for item in flow.get("frontend", {}).get(target_id, [])
        }
        missing = sorted(assigned - capability_ids)
        stale = sorted(capability_ids - assigned)
        for capability_id in missing:
            failures.append({"file": str(manifest_path), "target": capability_id, "reason": "flow catalog assigns capability but manifest does not define it"})
        for capability_id in stale:
            failures.append({"file": str(manifest_path), "target": capability_id, "reason": "manifest capability is not assigned by flow catalog"})
        capabilities_by_target[target_id] = capability_ids

    ledger_path = DELIVERY_ROOT / "changes" / "CONTRACT_CHANGES.yaml"
    ledger = _load_yaml(ledger_path)
    baseline_id = ledger.get("baseline_id")
    change_ids: set[str] = set()
    for change in ledger.get("changes", []):
        change_id = change.get("id")
        if not change_id or change_id in change_ids:
            failures.append({"file": str(ledger_path), "target": str(change_id), "reason": "missing or duplicate contract change id"})
            continue
        change_ids.add(change_id)
        unknown_flows = set(change.get("affected_flows", [])) - flow_ids
        for flow_id in sorted(unknown_flows):
            failures.append({"file": str(ledger_path), "target": flow_id, "reason": "contract change references unknown flow"})
        for target_id, capability_ids in change.get("affected_targets", {}).items():
            known = capabilities_by_target.get(target_id)
            if known is None:
                failures.append({"file": str(ledger_path), "target": target_id, "reason": "contract change references unknown target"})
                continue
            for capability_id in capability_ids:
                if capability_id not in known:
                    failures.append({"file": str(ledger_path), "target": capability_id, "reason": f"contract change capability is not assigned to {target_id}"})

    for status_file in sorted((DELIVERY_ROOT / "targets").rglob("STATUS.yaml")):
        status = _load_yaml(status_file)
        target_id = status.get("target")
        known = capabilities_by_target.get(target_id)
        if known is None:
            failures.append({"file": str(status_file), "target": str(target_id), "reason": "status registry references unknown frontend target"})
            continue
        recorded = {item.get("id"): item for item in status.get("capabilities", [])}
        if set(recorded) != known:
            failures.append({"file": str(status_file), "target": str(target_id), "reason": "status registry capability set differs from assigned manifest capabilities"})
        for capability_id, item in recorded.items():
            if item.get("status") not in VALID_CAPABILITY_STATUSES:
                failures.append({"file": str(status_file), "target": str(capability_id), "reason": "unknown capability status"})
        acknowledgement = status.get("last_acknowledged_change_id", baseline_id)
        if acknowledgement != baseline_id and acknowledgement not in change_ids:
            failures.append({"file": str(status_file), "target": str(acknowledgement), "reason": "unknown last acknowledged contract change id"})

    message_path = DELIVERY_ROOT / "catalogs" / "MESSAGE_CATALOG.yaml"
    message_ids: set[str] = set()
    for message in _load_yaml(message_path).get("messages", []):
        message_id = message.get("id")
        if not message_id or message_id in message_ids:
            failures.append({"file": str(message_path), "target": str(message_id), "reason": "missing or duplicate message id"})
            continue
        message_ids.add(message_id)
        contract = message.get("contract")
        if not contract or not _resolved(message_path.parent, contract).is_file():
            failures.append({"file": str(message_path), "target": str(contract), "reason": "missing message contract target"})

    operation_path = DELIVERY_ROOT / "catalogs" / "OPERATION_CATALOG.json"
    try:
        current = operation_path.read_text(encoding="utf-8")
        generated = render_operation_catalog(extract_rest_endpoints())
        operation_ids = [item["id"] for item in json.loads(current).get("operations", [])]
        if len(operation_ids) != len(set(operation_ids)):
            failures.append({"file": str(operation_path), "target": "operations", "reason": "duplicate operation id"})
        if current != generated:
            failures.append({"file": str(operation_path), "target": "operations", "reason": "generated REST catalog is stale; rerun export_rest_operation_catalog.py"})
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        failures.append({"file": str(operation_path), "target": "operations", "reason": f"cannot read generated operation catalog: {error}"})

    known_operation_ids = set(operation_ids) if "operation_ids" in locals() else set()
    for manifest_path in sorted((DELIVERY_ROOT / "targets").rglob("CONTRACT.yaml")):
        manifest = _load_yaml(manifest_path)
        target = manifest.get("target", {})
        references = list(target.get("operation_ids", []))
        for capability in manifest.get("capabilities", []):
            references.extend(capability.get("operation_ids", []))
        for operation_id in references:
            if operation_id not in known_operation_ids:
                failures.append({"file": str(manifest_path), "target": str(operation_id), "reason": "contract references an unknown generated operation id"})

    return {
        "check": "implementation_contracts",
        "passed": not failures,
        "failure_count": len(failures),
        "truncated": len(failures) > max_failures,
        "failures": failures[:max_failures],
    }
