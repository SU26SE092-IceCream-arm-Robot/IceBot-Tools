import sys
from pathlib import Path
from typing import Any

tools_dir = Path(__file__).resolve().parent.parent.parent
log_analyzer_dir = tools_dir / "log-analyzer"

sys.path.append(str(log_analyzer_dir))

from analyzer import (
    DEFAULT_MOCK_LOG_ROOT,
    DEFAULT_RAG_LOG_ROOT,
    DEFAULT_VIOLATIONS_LOG_PATH,
    LogAnalyzer,
)


def analyze_icebot_logs(
    webapi_path: str | None = None,
    robot_path: str | None = None,
    rag_path: str | None = None,
    include_rag: bool = False,
    max_items: int = 5,
) -> dict[str, Any]:
    """Analyze logs once with capped output. Quiet when clean, structured when issues exist."""
    analyzer = LogAnalyzer(
        webapi_path or str(DEFAULT_MOCK_LOG_ROOT / "webapi"),
        robot_path or str(DEFAULT_MOCK_LOG_ROOT / "robot"),
        rag_path or str(DEFAULT_RAG_LOG_ROOT),
        str(DEFAULT_VIOLATIONS_LOG_PATH),
        write_violations=False,
        verbose=False,
    )

    return analyzer.analyze_once(include_rag=include_rag, max_items=max_items)
