import argparse
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.delivery_contracts import (
    evidence_presence,
    find_target_manifest,
    load_yaml,
    resolve_target_repository,
    selected_capabilities,
    status_path,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create deterministic evidence inventory for an IceBot target; never auto-marks capability complete."
    )
    parser.add_argument("--target", required=True, help="Manifest id, for example IceBot-WebApp")
    parser.add_argument("--id", action="append", default=[], help="Optional FLOW-* or CAP-* id; repeatable")
    parser.add_argument("--output", type=Path, help="Markdown output path; stdout when omitted")
    args = parser.parse_args()

    manifest_path, manifest, kind = find_target_manifest(args.target)
    if kind != "frontend":
        raise ValueError("Evidence audit currently supports frontend manifests with capability definitions.")
    target = manifest["target"]
    repository_root = resolve_target_repository(manifest_path, target)
    if not repository_root.is_dir():
        raise ValueError(f"Target repository is unavailable: {repository_root}")
    status_file = status_path(args.target)
    status = load_yaml(status_file) if status_file.is_file() else {}
    known_status = {item.get("id"): item for item in status.get("capabilities", [])}

    lines = [
        f"# Candidate Evidence Audit: {args.target}",
        "",
        "This is deterministic path evidence only. It never proves correct API use, role scope, lifecycle, or failure behavior.",
        "Use it as the source inspection checklist for an AI/reviewer.",
        "",
        f"- Repository: `{repository_root}`",
        f"- Shared status: `{status_file}`",
        f"- Last acknowledged contract change: `{status.get('last_acknowledged_change_id', 'not recorded')}`",
        "",
    ]
    for capability in selected_capabilities(manifest, set(args.id)):
        found, missing = evidence_presence(repository_root, capability.get("evidence_targets", []))
        declared_status = known_status.get(capability["id"], {}).get("status", "not-recorded")
        lines.extend(
            [
                f"## {capability['id']}",
                "",
                f"- Declared status: `{declared_status}`",
                f"- Flow: `{capability['flow']}`",
                f"- Candidate paths found: {', '.join(f'`{item}`' for item in found) or 'none'}",
                f"- Candidate paths absent: {', '.join(f'`{item}`' for item in missing) or 'none'}",
                f"- Required states to verify: {', '.join(capability.get('required_states', []))}",
                "",
            ]
        )
    report = "\n".join(lines)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8", newline="\n")
        print(f"Wrote candidate evidence audit to {output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
