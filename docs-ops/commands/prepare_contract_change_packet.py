import argparse
from pathlib import Path

from _bootstrap import bootstrap_imports

bootstrap_imports()

from docsops.delivery_contracts import changes_after_acknowledgement, find_target_manifest, load_yaml, status_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a target-specific packet of confirmed contract changes not yet acknowledged."
    )
    parser.add_argument("--target", required=True, help="Manifest id, for example IceBot-WebApp")
    parser.add_argument("--output", type=Path, help="Markdown output path; stdout when omitted")
    args = parser.parse_args()

    _, _, _ = find_target_manifest(args.target)
    status_file = status_path(args.target)
    status = load_yaml(status_file) if status_file.is_file() else {}
    changes = changes_after_acknowledgement(args.target, status)
    lines = [
        f"# Contract Change Packet: {args.target}",
        "",
        f"Last acknowledged change: `{status.get('last_acknowledged_change_id', 'not recorded')}`",
        "",
    ]
    if not changes:
        lines.append("No confirmed contract changes require this target's review after its recorded acknowledgement.")
    for change in changes:
        affected = change["affected_targets"][args.target]
        lines.extend(
            [
                f"## {change['id']}: {change['title']}",
                "",
                f"- Flows: {', '.join(change.get('affected_flows', []))}",
                f"- Capabilities to review: {', '.join(affected)}",
                f"- Impact: {change['impact']}",
                "- Required review:",
                *[f"  - {item}" for item in change.get("required_review", [])],
                f"- Compatibility: {change.get('compatibility', 'not declared')}",
                "",
            ]
        )
    packet = "\n".join(lines)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(packet, encoding="utf-8", newline="\n")
        print(f"Wrote contract change packet to {output}")
    else:
        print(packet)


if __name__ == "__main__":
    main()
