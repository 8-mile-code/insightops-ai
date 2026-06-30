from typing import Any, Literal, TypedDict


AnalyticsAction = Literal[
    "daily_revenue",
    "orders_by_status",
    "failed_payments",
    "top_customers",
    "unknown",
]


class AnalyticsAgentState(TypedDict):
    question: str

    project_id: int | None
    dataset_id: int | None
    pipeline_run_id: int | None

    action: AnalyticsAction

    tool_result: Any
    answer: str
