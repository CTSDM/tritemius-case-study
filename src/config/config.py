from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # postgres
    postgres_user: str = "test"
    postgres_password: str = "test"
    postgres_db: str = "test"
    postgres_host: str = "localhost"
    postgres_external_port: str = "5432"
    # rabbitmq
    rabbitmq_queue_port: int = 5672
    rabbitmq_host: str = "localhost"
    rabbitmq_max_channels: int = 10

    # oracle ml
    risk_threshold: float = 0.8
    calculation_time_min_ms: int = 50
    calculation_time_max_ms: int = 500
    use_dummy: bool = True

    @computed_field
    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_external_port}/{self.postgres_db}"


settings = Settings()  # type: ignore
