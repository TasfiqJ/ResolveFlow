from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["snapshot", "local", "ci", "public"] = "snapshot"
    database_url: str = "postgresql+asyncpg://resolveflow:resolveflow@localhost:5432/resolveflow"
    build_id: str = "foundation-v1"
    git_sha: str = "uncommitted"
    cohere_allow_live: bool = False
    public_live_mode: bool = False
    slack_signing_secret: str | None = None
    jira_api_token: str | None = None

    @model_validator(mode="after")
    def reject_public_credentials(self) -> Settings:
        if self.environment == "public" and (self.slack_signing_secret or self.jira_api_token):
            raise ValueError("public mode must not contain Slack or Jira write credentials")
        if self.public_live_mode and not self.cohere_allow_live:
            raise ValueError("public live mode requires explicitly enabled live provider mode")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
