from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_external_port: str
    # rabbitmq
    rabbitmq_queue_port: int
    rabbitmq_host: str
    rabbitmq_max_channels: int

    # oracle ml
    risk_threshold: float
    calculation_time_min_ms: int
    calculation_time_max_ms: int

    @computed_field
    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_external_port}/{self.postgres_db}"


settings = Settings()  # type: ignore
