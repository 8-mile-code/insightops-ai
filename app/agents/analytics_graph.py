import re
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.analytics_state import AnalyticsAction, AnalyticsAgentState
from app.agents.analytics_tools import (
    get_daily_revenue_tool,
    get_failed_payments_tool,
    get_orders_by_status_tool,
    get_top_customers_tool,
)


def parse_question(
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    question = state["question"]

    return {
        "project_id": _extract_int(question, "project"),
        "dataset_id": _extract_int(question, "dataset"),
        "pipeline_run_id": _extract_pipeline_run_id(question),
    }


def choose_action(
    state: AnalyticsAgentState,
) -> dict[str, AnalyticsAction]:
    question = state["question"].lower()

    if "revenue" in question or "выруч" in question:
        return {"action": "daily_revenue"}

    if "status" in question or "статус" in question:
        return {"action": "orders_by_status"}

    if "failed" in question or "ошиб" in question or "платеж" in question:
        return {"action": "failed_payments"}

    if "top customer" in question or "customers" in question:
        return {"action": "top_customers"}

    if "топ клиент" in question or "клиент" in question:
        return {"action": "top_customers"}

    return {"action": "unknown"}


def execute_analytics_query(
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    action = state["action"]

    if action == "unknown":
        return {
            "tool_result": {
                "error": "I could not choose an analytics action."
            }
        }

    project_id = state["project_id"]

    if project_id is None:
        return {
            "tool_result": {
                "error": "project_id is required. Example: project 1"
            }
        }

    dataset_id = state["dataset_id"]
    pipeline_run_id = state["pipeline_run_id"]

    if action == "daily_revenue":
        result = get_daily_revenue_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        return {"tool_result": result}

    if action == "orders_by_status":
        result = get_orders_by_status_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        return {"tool_result": result}

    if action == "failed_payments":
        result = get_failed_payments_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        return {"tool_result": result}

    if action == "top_customers":
        result = get_top_customers_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            limit=5,
        )
        return {"tool_result": result}

    return {
        "tool_result": {
            "error": "I could not execute the selected analytics action."
        }
    }


def generate_answer(
    state: AnalyticsAgentState,
) -> dict[str, str]:
    action = state["action"]
    result = state["tool_result"]

    if isinstance(result, dict) and "error" in result:
        return {"answer": result["error"]}

    if action == "daily_revenue":
        return {"answer": _format_daily_revenue(result)}

    if action == "orders_by_status":
        return {"answer": _format_orders_by_status(result)}

    if action == "failed_payments":
        return {"answer": _format_failed_payments(result)}

    if action == "top_customers":
        return {"answer": _format_top_customers(result)}

    return {"answer": "I do not know how to answer this question yet."}


def build_analytics_agent():
    graph = StateGraph(AnalyticsAgentState)

    graph.add_node("parse_question", parse_question)
    graph.add_node("choose_action", choose_action)
    graph.add_node("execute_analytics_query", execute_analytics_query)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "parse_question")
    graph.add_edge("parse_question", "choose_action")
    graph.add_edge("choose_action", "execute_analytics_query")
    graph.add_edge("execute_analytics_query", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


def _extract_int(question: str, label: str) -> int | None:
    pattern = rf"{label}\s+(\d+)"
    match = re.search(pattern, question.lower())

    if match is None:
        return None

    return int(match.group(1))


def _extract_pipeline_run_id(question: str) -> int | None:
    patterns = [
        r"pipeline\s+run\s+(\d+)",
        r"pipeline_run_id\s*=\s*(\d+)",
        r"run\s+(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question.lower())

        if match is not None:
            return int(match.group(1))

    return None


def _format_daily_revenue(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No daily revenue data found."

    lines = ["Daily revenue:"]

    for row in rows:
        lines.append(f"- {row['date']}: {row['revenue']:.2f}")

    return "\n".join(lines)


def _format_orders_by_status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No orders by status data found."

    lines = ["Orders by status:"]

    for row in rows:
        lines.append(f"- {row['status']}: {row['orders_count']} orders")

    return "\n".join(lines)


def _format_failed_payments(result: dict[str, Any]) -> str:
    return (
        "Failed payments: "
        f"{result['failed_count']} payments, "
        f"amount {result['failed_amount']:.2f}"
    )


def _format_top_customers(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No top customers data found."

    lines = ["Top customers:"]

    for index, row in enumerate(rows, start=1):
        lines.append(
            f"{index}. Customer {row['customer_id']}: "
            f"{row['revenue']:.2f}"
        )

    return "\n".join(lines)
