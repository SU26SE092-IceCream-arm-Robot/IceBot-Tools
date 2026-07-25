from __future__ import annotations

from pathlib import Path

import yaml

from toolcore.workspace import WORKSPACE_ROOT


PRODUCT_ROOT = WORKSPACE_ROOT / "IceBot-Product"
DELIVERY_ROOT = PRODUCT_ROOT / "delivery"
TARGETS_ROOT = DELIVERY_ROOT / "targets"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def find_target_manifest(target_id: str) -> tuple[Path, dict, str]:
    for path in sorted(TARGETS_ROOT.rglob("CONTRACT.yaml")):
        document = load_yaml(path)
        target = document.get("target", {})
        if target.get("id") == target_id:
            return path, document, target.get("kind", "unknown")
    raise ValueError(f"No target contract has id '{target_id}'.")


def status_path(target_id: str) -> Path:
    manifest_path, _, _ = find_target_manifest(target_id)
    return manifest_path.parent / "STATUS.yaml"


def resolve_target_repository(manifest_path: Path, target: dict) -> Path:
    configured_path = target.get("repository_path")
    if not configured_path:
        raise ValueError("Target manifest does not declare repository_path.")
    return (manifest_path.parent / configured_path).resolve()


def selected_capabilities(manifest: dict, requested_ids: set[str]) -> list[dict]:
    capabilities = manifest.get("capabilities", [])
    if not requested_ids:
        return capabilities
    selected = [
        capability
        for capability in capabilities
        if capability.get("id") in requested_ids or capability.get("flow") in requested_ids
    ]
    if not selected:
        raise ValueError("None of the requested IDs apply to the selected target.")
    return selected


def evidence_presence(repository_root: Path, evidence_targets: list[str]) -> tuple[list[str], list[str]]:
    found: list[str] = []
    missing: list[str] = []
    for evidence_target in evidence_targets:
        path = repository_root.joinpath(*evidence_target.split("/"))
        (found if path.exists() else missing).append(evidence_target)
    return found, missing


def changes_after_acknowledgement(target_id: str, status: dict) -> list[dict]:
    ledger = load_yaml(DELIVERY_ROOT / "changes" / "CONTRACT_CHANGES.yaml")
    baseline_id = ledger.get("baseline_id")
    acknowledged = status.get("last_acknowledged_change_id", baseline_id)
    changes = ledger.get("changes", [])
    ids = [change.get("id") for change in changes]
    if acknowledged == baseline_id:
        candidates = changes
    elif acknowledged in ids:
        candidates = changes[ids.index(acknowledged) + 1 :]
    else:
        raise ValueError(f"Unknown last acknowledged change id '{acknowledged}'.")
    return [change for change in candidates if target_id in change.get("affected_targets", {})]
