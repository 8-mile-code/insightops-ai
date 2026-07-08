import asyncio
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_tool(
    session: ClientSession,
    tool_name: str,
    arguments: dict[str, Any],
) -> None:
    result = await session.call_tool(
        tool_name,
        arguments=arguments,
    )

    print("=" * 80)
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")

    if result.structuredContent is not None:
        print("Structured result:")
        print(result.structuredContent)
        return

    print("Raw result:")
    print(result.content)


async def main() -> None:
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "-m",
            "app.mcp_servers.analytics_server",
        ],
        env={
            **os.environ,
            "CLICKHOUSE_HOST": os.environ.get(
                "CLICKHOUSE_HOST",
                "localhost",
            ),
            "CLICKHOUSE_PORT": os.environ.get("CLICKHOUSE_PORT", "8123"),
            "CLICKHOUSE_DB": os.environ.get(
                "CLICKHOUSE_DB",
                "insightops_analytics",
            ),
            "CLICKHOUSE_USER": os.environ.get(
                "CLICKHOUSE_USER",
                "insightops",
            ),
            "CLICKHOUSE_PASSWORD": os.environ.get(
                "CLICKHOUSE_PASSWORD",
                "clickhouse",
            ),
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available MCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            await call_tool(
                session,
                "get_daily_revenue",
                {
                    "project_id": 2,
                    "pipeline_run_id": 13,
                },
            )

            await call_tool(
                session,
                "get_failed_payments",
                {
                    "project_id": 2,
                    "pipeline_run_id": 13,
                },
            )

            await call_tool(
                session,
                "get_top_customers",
                {
                    "project_id": 2,
                    "pipeline_run_id": 13,
                    "limit": 5,
                },
            )

            await call_tool(
                session,
                "get_pipeline_status",
                {
                    "pipeline_run_id": 13,
                },
            )


if __name__ == "__main__":
    asyncio.run(main())
