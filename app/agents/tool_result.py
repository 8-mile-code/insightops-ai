from typing import Any, TypedDict


class ToolResult(TypedDict):
    tool_name: str
    data: Any
    sources: list[dict[str, Any]]
    metadata: dict[str, Any]
