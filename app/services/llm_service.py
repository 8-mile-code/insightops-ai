from typing import Any

from openai import APIError, AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.prompts.report_summary import build_report_prompt


class LLMService:
    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.enabled = settings.LLM_ENABLED
        self.api_key = settings.OPENAI_API_KEY

    async def generate_report_summary(
        self,
        metrics: dict[str, Any],
    ) -> str:
        if not self.enabled:
            raise LLMServiceError("LLM generation is disabled.")

        if self.provider != "openai":
            raise LLMServiceError(f"Unsupported LLM provider: {self.provider}")

        if not self.api_key:
            raise LLMServiceError("OPENAI_API_KEY is not configured.")

        prompt = build_report_prompt(metrics)

        try:
            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.responses.create(
                model=self.model,
                input=prompt,
            )

            content = response.output_text.strip()

            if not content:
                raise LLMServiceError("LLM returned an empty response.")

            return content

        except (OpenAIError, APIError) as error:
            raise LLMServiceError(
                "OpenAI report generation failed."
            ) from error
