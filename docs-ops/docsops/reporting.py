def format_failure_item(check_name: str, item: dict) -> str:
    file_path = item.get("file")
    line = item.get("line")
    location = f"{file_path}:{line}" if line is not None else str(file_path)

    if check_name == "stale_refs":
        return f"- {location} contains '{item.get('pattern')}': {item.get('text')}"

    target = item.get("target")
    reason = item.get("reason")
    if target:
        return f"- {location} -> {target} ({reason})"

    return f"- {location} ({reason})"


def format_check_failure(check: dict) -> list[str]:
    lines = [f"[{check['check']}] {check['failure_count']} issue(s)"]
    lines.extend(format_failure_item(check["check"], item) for item in check["failures"])

    if check.get("truncated"):
        lines.append("- ... additional failures truncated")

    return lines


def format_aggregate_cli_report(result: dict) -> list[str]:
    if result["passed"]:
        return [result["summary"]]

    lines = [result["summary"]]
    for check in result["checks"]:
        if check["passed"]:
            continue

        lines.append("")
        lines.extend(format_check_failure(check))

    return lines
