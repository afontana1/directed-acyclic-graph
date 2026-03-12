from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend API."""

    model_config = SettingsConfigDict(env_prefix="DAG_API_", case_sensitive=False)

    title: str = "Directed Acyclic Graph API"
    version: str = "0.1.0"
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    create_default_graph: bool = True
    default_graph_id: str = "default"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
