import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.delivery_contracts import DELIVERY_ROOT, find_target_manifest, load_yaml
from toolcore.workspace import WORKSPACE_ROOT


def _selected_flows(catalog: dict, requested: set[str], target_id: str, related_flow_ids: set[str]) -> list[dict]:
    selected: list[dict] = []
    for flow in catalog.get("flows", []):
        frontend = flow.get("frontend", {})
        capability_ids = set(frontend.get(target_id, []))
        if requested:
            if flow["id"] in requested or capability_ids & requested:
                selected.append(flow)
        elif capability_ids or flow["id"] in related_flow_ids:
            selected.append(flow)
    return selected


def _operations_summary(operations: dict, operation_ids: list[str]) -> str:
    return ", ".join(
        f"{operations[item]['method']} {operations[item]['route']} ({item})"
        for item in operation_ids
    ) or "No REST operation assigned yet."


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a focused IceBot implementation context packet from product contracts."
    )
    parser.add_argument("--target", required=True, help="Manifest ID, for example IceBot-Kiosk, IceBot-Mobile, or IceBot-IOT")
    parser.add_argument("--id", action="append", default=[], help="Optional FLOW-* or CAP-* ID; repeatable")
    parser.add_argument("--output", type=Path, help="Optional Markdown output path; stdout when omitted")
    args = parser.parse_args()

    manifest_path, manifest, kind = find_target_manifest(args.target)
    catalog = load_yaml(DELIVERY_ROOT / "catalogs" / "FLOW_CATALOG.yaml")
    operation_catalog = json.loads((DELIVERY_ROOT / "catalogs" / "OPERATION_CATALOG.json").read_text(encoding="utf-8"))
    operations = {item["id"]: item for item in operation_catalog.get("operations", [])}
    requested = set(args.id)
    target = manifest["target"]
    flows = _selected_flows(catalog, requested, args.target, set(target.get("related_flows", [])))
    if requested and not flows:
        raise ValueError("None of the requested IDs apply to the selected target.")

    lines = [
        f"# IceBot Implementation Packet: {args.target}",
        "",
        "Generated navigation only. Inspect the target repository before declaring any status.",
        "",
        "## Target",
        "",
        f"- Manifest: `{manifest_path.relative_to(WORKSPACE_ROOT).as_posix()}`",
        f"- Repository: `{target.get('repository_path', 'not declared')}`",
        f"- Audience: {target.get('audience', 'not declared')}",
        "",
        "## Read Order",
        "",
        "1. `IceBot-Product/delivery/playbooks/ROLE_IMPLEMENTATION_CONTRACT.md`",
        f"2. `{manifest_path.relative_to(WORKSPACE_ROOT).as_posix()}`",
        "3. Each selected FLOW entry and its linked product/backend documents",
        "4. `delivery/catalogs/OPERATION_CATALOG.json` or `MESSAGE_CATALOG.yaml` only for exact integration lookup",
        "5. Current target repository code and tests",
        "",
        "## Applicable Flows",
        "",
    ]
    for flow in flows:
        capabilities = flow.get("frontend", {}).get(args.target, [])
        lines.extend(
            [
                f"### {flow['id']}: {flow['title']}",
                f"- Product journey: `{flow['product_journey']}`",
                f"- Backend flow: `{flow['backend_flow']}`",
                f"- Target capabilities: {', '.join(capabilities) if capabilities else 'role-level responsibility'}",
                "",
            ]
        )

    if kind == "frontend":
        lines.extend(["## Capability Evidence Targets", ""])
        for capability in manifest.get("capabilities", []):
            if requested and capability["id"] not in requested and capability["flow"] not in requested:
                continue
            lines.extend(
                [
                    f"### {capability['id']}",
                    f"- Flow: {capability['flow']}",
                    f"- Actor/scope: {capability['actor']} / {capability['scope']}",
                    f"- Required states: {', '.join(capability['required_states'])}",
                    f"- Operations: {_operations_summary(operations, capability.get('operation_ids', []))}",
                    f"- Inspect: {', '.join(capability['evidence_targets'])}",
                    "",
                ]
            )
    else:
        lines.extend(["## Role Responsibilities", ""])
        lines.extend(f"- {item}" for item in target.get("responsibilities", []))
        lines.extend(["", "## Cloud Operations", ""])
        lines.extend(f"- `{operations[item]['method']} {operations[item]['route']}` ({item})" for item in target.get("operation_ids", []))
        lines.extend(["", "## Evidence Targets", ""])
        lines.extend(f"- `{item}`" for item in target.get("evidence_targets", []))

    lines.extend(
        [
            "",
            "## Required Audit Output",
            "",
            "Use `AI_IMPLEMENTATION_REQUEST.md`: status with file/symbol evidence,"
            " missing behavior, implementable task, and acceptance evidence. Do not infer"
            " completion from a screen, mock, type, or service stub.",
            "",
        ]
    )
    output = "\n".join(lines)
    if args.output:
        path = args.output.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8", newline="\n")
        print(f"Wrote implementation packet to {path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
