import logging
import re
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.analytics_state import AnalyticsAction, AnalyticsAgentState
from app.agents.analytics_tools import (
    compare_periods_tool,
    generate_report_tool,
    get_daily_revenue_tool,
    get_failed_payments_tool,
    get_orders_by_status_tool,
    get_top_customers_tool,
)
from app.agents.tool_result import ToolResult
from app.core.exceptions import MCPToolCallError
from app.mcp_clients.analytics_client import AnalyticsMCPClient

logger = logging.getLogger(__name__)


def parse_question(
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    question = state["question"]

    extracted_project_id = _extract_int(question, "project")
    extracted_dataset_id = _extract_int(question, "dataset")
    extracted_pipeline_run_id = _extract_pipeline_run_id(question)

    return {
        "project_id": extracted_project_id or state.get("project_id"),
        "dataset_id": extracted_dataset_id or state.get("dataset_id"),
        "pipeline_run_id": (
            extracted_pipeline_run_id or state.get("pipeline_run_id")
        ),
    }


def choose_action(
    state: AnalyticsAgentState,
) -> dict[str, AnalyticsAction]:
    question = state["question"].lower()

    if "compare" in question or "сравн" in question:
        return {"action": "compare_periods"}

    if "report" in question or "отчет" in question or "summary" in question:
        return {"action": "generate_report"}

    if (
        "pipeline status" in question
        or "run status" in question
        or "статус пайплайна" in question
        or "статус запуска" in question
    ):
        return {"action": "pipeline_status"}

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


async def execute_analytics_query(
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    action = state["action"]

    logger.info(
        "agent_action_selected",
        extra={
            "agent_action": action,
            "project_id": state.get("project_id"),
            "dataset_id": state.get("dataset_id"),
            "pipeline_run_id": state.get("pipeline_run_id"),
        },
    )

    if action == "unknown":
        return {
            "tool_result": {"error": "I could not choose an analytics action."}
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

    common_arguments = {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "pipeline_run_id": pipeline_run_id,
    }

    if action == "daily_revenue":
        return await _call_mcp_tool_with_fallback(
            mcp_tool_name="get_daily_revenue",
            mcp_arguments=common_arguments,
            fallback_tool=get_daily_revenue_tool,
            fallback_arguments=common_arguments,
            state=state,
        )

    if action == "orders_by_status":
        result = get_orders_by_status_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        return _build_tool_state_update(result, state)

    if action == "failed_payments":
        return await _call_mcp_tool_with_fallback(
            mcp_tool_name="get_failed_payments",
            mcp_arguments=common_arguments,
            fallback_tool=get_failed_payments_tool,
            fallback_arguments=common_arguments,
            state=state,
        )

    if action == "top_customers":
        arguments = {
            **common_arguments,
            "limit": 5,
        }
        return await _call_mcp_tool_with_fallback(
            mcp_tool_name="get_top_customers",
            mcp_arguments=arguments,
            fallback_tool=get_top_customers_tool,
            fallback_arguments=arguments,
            state=state,
        )

    if action == "compare_periods":
        compare_pipeline_run_id = state["compare_pipeline_run_id"]

        if pipeline_run_id is None or compare_pipeline_run_id is None:
            return {
                "tool_result": {
                    "error": (
                        "To compare periods, provide pipeline_run_id "
                        "and compare_pipeline_run_id."
                    )
                },
                "used_tools": [],
                "sources": [],
            }

        result = compare_periods_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            compare_pipeline_run_id=compare_pipeline_run_id,
        )
        return _build_tool_state_update(result, state)

    if action == "generate_report":
        result = generate_report_tool(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        return _build_tool_state_update(result, state)

    if action == "pipeline_status":
        if pipeline_run_id is None:
            return {
                "tool_result": {
                    "error": "pipeline_run_id is required. Example: run 13"
                },
                "used_tools": [],
                "sources": [],
            }

        mcp_client = AnalyticsMCPClient()
        mcp_result = await mcp_client.call_tool(
            "get_pipeline_status",
            {
                "project_id": project_id,
                "pipeline_run_id": pipeline_run_id,
            },
        )
        logger.info(
            "agent_mcp_tool_executed",
            extra={
                "tool_name": "get_pipeline_status",
                "agent_action": state.get("action"),
                "project_id": state.get("project_id"),
                "dataset_id": state.get("dataset_id"),
                "pipeline_run_id": state.get("pipeline_run_id"),
            },
        )

        return {
            "tool_result": _normalize_mcp_result(
                tool_name="get_pipeline_status",
                result=mcp_result,
            ),
            "used_tools": ["get_pipeline_status"],
            "sources": mcp_result.get("sources", []),
        }


def generate_answer(
    state: AnalyticsAgentState,
) -> dict[str, str]:
    action = state["action"]
    result = state["tool_result"]

    if isinstance(result, dict) and "error" in result:
        return {"answer": result["error"]}

    data = result["data"]

    if action == "daily_revenue":
        return {"answer": _format_daily_revenue(data)}

    if action == "orders_by_status":
        return {"answer": _format_orders_by_status(data)}

    if action == "failed_payments":
        return {"answer": _format_failed_payments(data)}

    if action == "top_customers":
        return {"answer": _format_top_customers(data)}

    if action == "compare_periods":
        return {"answer": _format_compare_periods(data)}

    if action == "pipeline_status":
        return {"answer": _format_pipeline_status(data)}

    if action == "generate_report":
        return {"answer": data["summary"]}

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
            f"{index}. Customer {row['customer_id']}: {row['revenue']:.2f}"
        )

    return "\n".join(lines)


def _format_compare_periods(data: dict[str, Any]) -> str:
    diff_percent = data["difference_percent"]

    percent_part = (
        f" ({diff_percent:.2f}%)"
        if diff_percent is not None
        else " (percentage change is unavailable "
        "because previous revenue is 0)"
    )

    return (
        "Revenue comparison:\n"
        f"- Current pipeline run {data['current_pipeline_run_id']}: "
        f"{data['current_total_revenue']:.2f}\n"
        f"- Compared pipeline run {data['compare_pipeline_run_id']}: "
        f"{data['previous_total_revenue']:.2f}\n"
        f"- Difference: {data['difference']:.2f}{percent_part}"
    )


def _format_pipeline_status(data: dict[str, Any]) -> str:
    return (
        "Pipeline status:\n"
        f"- Pipeline run ID: {data['pipeline_run_id']}\n"
        f"- Status: {data['status']}\n"
        f"- Message: {data.get('message', 'No details')}"
    )


def _build_tool_state_update(
    tool_result: ToolResult,
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    tool_name = tool_result["tool_name"]

    logger.info(
        "agent_tool_executed",
        extra={
            "tool_name": tool_name,
            "agent_action": state.get("action"),
            "project_id": state.get("project_id"),
            "dataset_id": state.get("dataset_id"),
            "pipeline_run_id": state.get("pipeline_run_id"),
        },
    )

    return {
        "tool_result": tool_result,
        "used_tools": [tool_name],
        "sources": tool_result["sources"],
    }


async def _call_mcp_tool_with_fallback(
    *,
    mcp_tool_name: str,
    mcp_arguments: dict[str, Any],
    fallback_tool,
    fallback_arguments: dict[str, Any],
    state: AnalyticsAgentState,
) -> dict[str, Any]:
    mcp_client = AnalyticsMCPClient()

    try:
        mcp_result = await mcp_client.call_tool(
            mcp_tool_name,
            mcp_arguments,
        )

        logger.info(
            "agent_mcp_tool_executed",
            extra={
                "tool_name": mcp_tool_name,
                "agent_action": state.get("action"),
                "project_id": state.get("project_id"),
                "dataset_id": state.get("dataset_id"),
                "pipeline_run_id": state.get("pipeline_run_id"),
            },
        )

        return {
            "tool_result": _normalize_mcp_result(
                tool_name=mcp_tool_name,
                result=mcp_result,
            ),
            "used_tools": [mcp_tool_name],
            "sources": mcp_result.get("sources", []),
        }

    except MCPToolCallError as error:
        logger.warning(
            "MCP tool failed, falling back to direct tool: %s",
            mcp_tool_name,
            exc_info=error,
        )

        fallback_result = fallback_tool(**fallback_arguments)
        fallback_result["metadata"]["fallback_reason"] = str(error)

        logger.warning(
            "agent_tool_fallback_used",
            extra={
                "tool_name": fallback_result["tool_name"],
                "agent_action": state.get("action"),
                "project_id": state.get("project_id"),
                "dataset_id": state.get("dataset_id"),
                "pipeline_run_id": state.get("pipeline_run_id"),
            },
        )

        return {
            "tool_result": fallback_result,
            "used_tools": [
                f"fallback:{fallback_result['tool_name']}",
            ],
            "sources": fallback_result["sources"],
        }


def _normalize_mcp_result(
    *,
    tool_name: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "tool_name": result.get("tool", tool_name),
        "data": result.get("data"),
        "sources": result.get("sources", []),
        "metadata": {
            **result.get("metadata", {}),
            "execution_layer": "mcp",
        },
    }
