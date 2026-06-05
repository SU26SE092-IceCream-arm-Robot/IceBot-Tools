import json
from pathlib import Path

from raglib.config import TOOLS_DIR


def load_source_configs(collection_lane: dict, logger, missing_source_message: str) -> list[dict]:
    sources_local_path = collection_lane["sources_local_path"]
    sources_example_path = collection_lane["sources_example_path"]
    source_config_path = sources_local_path if sources_local_path.exists() else sources_example_path
    source_config_message = f"Using source config: {source_config_path}"
    logger.info(source_config_message)
    print(source_config_message)

    if not source_config_path.exists():
        raise SystemExit(
            f"Missing source config: {source_config_path}\n"
            f"{missing_source_message}"
        )

    try:
        raw_sources = json.loads(source_config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise SystemExit(f"Invalid JSON source config: {source_config_path}\n{ex}") from ex

    if not isinstance(raw_sources, list):
        raise SystemExit(f"Source config must be a JSON array: {source_config_path}")

    source_configs = []

    for index, source in enumerate(raw_sources):
        if not isinstance(source, dict):
            raise SystemExit(f"Source config item #{index + 1} must be an object.")

        missing_fields = [
            field_name for field_name in ("path", "source_type", "authority", "status")
            if not source.get(field_name)
        ]

        if missing_fields:
            raise SystemExit(
                f"Source config item #{index + 1} is missing: {', '.join(missing_fields)}"
            )

        source_path = Path(source["path"])

        if not source_path.is_absolute():
            source_path = TOOLS_DIR / source_path

        source_configs.append(
            {
                **source,
                "path": source_path.resolve(),
                "required": bool(source.get("required", False)),
            }
        )

    return source_configs


def validate_source_paths(source_configs: list[dict]) -> None:
    missing_required_sources = [
        source_config["path"]
        for source_config in source_configs
        if source_config["required"] and not source_config["path"].exists()
    ]

    if not missing_required_sources:
        return

    formatted_paths = "\n".join(f"- {source_path}" for source_path in missing_required_sources)
    raise SystemExit(f"Missing required RAG source(s):\n{formatted_paths}")
