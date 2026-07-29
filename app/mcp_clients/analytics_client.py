import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings
from app.core.exceptions import MCPToolCallError


class AnalyticsMCPClient:
    def _get_server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command="uv",
            args=[
                "run",
                "python",
                "-m",
                "app.mcp_servers.analytics_server",
            ],
            env={
                **os.environ,
                # MCP stdio reserves stdout for JSON-RPC messages.
                "DEBUG": "false",
                "CLICKHOUSE_HOST": settings.CLICKHOUSE_HOST,
                "CLICKHOUSE_PORT": str(settings.CLICKHOUSE_PORT),
                "CLICKHOUSE_DB": settings.CLICKHOUSE_DB,
                "CLICKHOUSE_USER": settings.CLICKHOUSE_USER,
                "CLICKHOUSE_PASSWORD": settings.CLICKHOUSE_PASSWORD,
            },
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            server_params = self._get_server_params()

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        tool_name,
                        arguments=arguments,
                    )
                    if result.isError:
                        raise MCPToolCallError(
                            f"MCP tool returned an error: {tool_name}"
                        )

            if result.structuredContent is not None:
                return dict(result.structuredContent)

            return {
                "tool": tool_name,
                "data": result.content,
                "sources": [],
                "metadata": {
                    "response_type": "raw_content",
                },
            }

        except MCPToolCallError:
            raise
        except Exception as error:
            raise MCPToolCallError(
                f"MCP tool call failed: {tool_name}"
            ) from error
