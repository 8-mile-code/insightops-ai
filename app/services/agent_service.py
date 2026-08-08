from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.analytics_graph import build_analytics_agent
from app.models.agent_message import AgentMessage
from app.models.report import Report
from app.models.user import User
from app.repositories.agent_message_repository import AgentMessageRepository
from app.schemas.agent import AskRequest
from app.schemas.report import ReportGenerateRequest
from app.services.project_service import ProjectService
from app.services.report_service import ReportService


class AgentService:
    def __init__(
        self,
        *,
        project_service: ProjectService,
        message_repo: AgentMessageRepository,
        report_service: ReportService,
    ) -> None:
        self.project_service = project_service
        self.message_repo = message_repo
        self.report_service = report_service

    async def ask(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        ask_in: AskRequest,
    ) -> AgentMessage:
        await self.project_service.get_user_project(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        if self._is_report_generation_request(ask_in.question):
            return await self._generate_report_from_question(
                db,
                project_id=project_id,
                current_user=current_user,
                ask_in=ask_in,
            )

        agent_result = await self._run_agent(
            project_id=project_id,
            ask_in=ask_in,
        )

        return await self.message_repo.create(
            db,
            project_id=project_id,
            dataset_id=ask_in.dataset_id,
            pipeline_run_id=ask_in.pipeline_run_id,
            question=ask_in.question,
            answer=agent_result["answer"],
            used_tools=agent_result.get("used_tools", []),
            sources=agent_result.get("sources", []),
        )

    async def get_project_messages(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> list[AgentMessage]:
        await self.project_service.get_user_project(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await self.message_repo.get_all_by_project(
            db,
            project_id=project_id,
        )

    async def _run_agent(
        self,
        *,
        project_id: int,
        ask_in: AskRequest,
    ) -> dict[str, Any]:
        agent = build_analytics_agent()

        initial_state = {
            "question": ask_in.question,
            "project_id": project_id,
            "dataset_id": ask_in.dataset_id,
            "pipeline_run_id": ask_in.pipeline_run_id,
            "compare_pipeline_run_id": ask_in.compare_pipeline_run_id,
            "action": "unknown",
            "tool_result": None,
            "used_tools": [],
            "sources": [],
            "answer": "",
        }

        return await agent.ainvoke(initial_state)

    def _is_report_generation_request(self, question: str) -> bool:
        normalized_question = question.lower()

        report_keywords = [
            "generate report",
            "create report",
            "business report",
            "weekly report",
            "summary report",
            "сгенерируй отчет",
            "создай отчет",
            "бизнес отчет",
            "аналитический отчет",
            "отчет",
        ]

        return any(
            keyword in normalized_question for keyword in report_keywords
        )

    async def _generate_report_from_question(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        ask_in: AskRequest,
    ) -> AgentMessage:
        report = await self.report_service.generate_report(
            db,
            project_id=project_id,
            current_user=current_user,
            report_in=ReportGenerateRequest(
                dataset_id=ask_in.dataset_id,
                pipeline_run_id=ask_in.pipeline_run_id,
            ),
        )

        answer = self._build_report_agent_answer(report)

        return await self.message_repo.create(
            db,
            project_id=project_id,
            dataset_id=ask_in.dataset_id,
            pipeline_run_id=ask_in.pipeline_run_id,
            report_id=report.id,
            question=ask_in.question,
            answer=answer,
            used_tools=[
                "report_service.generate_report",
                "analytics_service.collect_metrics",
                "llm_service.generate_report_summary",
            ],
            sources=[
                {
                    "type": "postgres_table",
                    "name": "reports",
                    "report_id": report.id,
                    "project_id": project_id,
                },
                {
                    "type": "analytics_context",
                    "project_id": project_id,
                    "dataset_id": ask_in.dataset_id,
                    "pipeline_run_id": ask_in.pipeline_run_id,
                },
            ],
        )

    def _build_report_agent_answer(self, report: Report) -> str:
        return (
            "Business report generated successfully.\n"
            f"Report ID: {report.id}\n"
            f"Title: {report.title}\n\n"
            f"{report.content}"
        )
