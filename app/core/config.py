from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_TITLE: str = "InsightOps AI"
    APP_DESCRIPTION: str = (
        "AI-powered backend platform for business data analytics"
    )
    DEBUG: bool = False
    DB_HOST: str
    DB_PORT: int
    POSTGRES_DB: str
    TEST_POSTGRES_DB: str = "insightops_test"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    AIRFLOW_API_BASE_URL: str = "http://localhost:8080"
    AIRFLOW_API_USERNAME: str = "admin"
    AIRFLOW_API_PASSWORD: str = "airflow"
    AIRFLOW_API_TIMEOUT_SECONDS: float = 10.0
    AIRFLOW_PROCESS_DATASET_DAG_ID: str = "process_dataset"

    CLICKHOUSE_HOST: str
    CLICKHOUSE_PORT: int
    CLICKHOUSE_DB: str
    CLICKHOUSE_USER: str
    CLICKHOUSE_PASSWORD: str

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-5.4-mini"
    LLM_ENABLED: bool = False
    OPENAI_API_KEY: str | None = None
    LLM_TIMEOUT_SECONDS: float = 15.0

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    REQUEST_ID_HEADER: str = "X-Request-ID"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def TEST_DATABASE_URL_ASYNC(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.TEST_POSTGRES_DB}"
        )


settings = Settings()
