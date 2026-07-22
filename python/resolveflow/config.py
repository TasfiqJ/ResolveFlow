from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RESOLVEFLOW_", extra="ignore")

    environment: Literal["snapshot", "local", "ci", "public"] = "snapshot"
    database_url: str = "postgresql+asyncpg://resolveflow:resolveflow@localhost:5432/resolveflow"
    build_id: str = "foundation-v1"
    git_sha: str = "uncommitted"
    cohere_allow_live: bool = False
    cohere_api_key: str | None = None
    cohere_command_model: str = "command-a-plus-05-2026"
    cohere_embed_model: str = "embed-v4.0"
    cohere_rerank_fast_model: str = "rerank-v4.0-fast"
    cohere_rerank_pro_model: str = "rerank-v4.0-pro"
    public_live_mode: bool = False
    public_live_daily_limit: int = 12
    public_live_session_limit: int = 2
    public_live_ip_limit: int = 4
    public_live_queue_limit: int = 4
    public_live_deadline_seconds: int = 45
    agent_max_tool_rounds: int = 2
    agent_max_provider_calls: int = 4
    agent_max_total_tokens: int = 4096
    agent_wall_clock_seconds: float = 30.0
    agent_tool_timeout_seconds: float = 2.0
    slack_signing_secret: str | None = None
    jira_api_token: str | None = None
    jira_base_url: str | None = None
    jira_project_key: str | None = None
    jira_real_enabled: bool = False
    jira_external_writes_authorized: bool = False
    action_dispatch_enabled: bool = False

    @model_validator(mode="after")
    def reject_public_credentials(self) -> Settings:
        if self.environment == "public" and (self.slack_signing_secret or self.jira_api_token):
            raise ValueError("public mode must not contain Slack or Jira write credentials")
        if self.public_live_mode and not self.cohere_allow_live:
            raise ValueError("public live mode requires explicitly enabled live provider mode")
        if self.cohere_allow_live and not self.cohere_api_key:
            raise ValueError("live Cohere mode requires an API key")
        if (
            min(
                self.public_live_daily_limit,
                self.public_live_session_limit,
                self.public_live_ip_limit,
                self.public_live_queue_limit,
                self.public_live_deadline_seconds,
            )
            < 1
        ):
            raise ValueError("public live quotas, queue, and deadline must be positive")
        if self.agent_max_provider_calls < 2 or self.agent_max_tool_rounds < 1:
            raise ValueError("governed agent budgets are invalid")
        if self.environment == "public" and (
            self.jira_real_enabled
            or self.jira_external_writes_authorized
            or self.action_dispatch_enabled
        ):
            raise ValueError("public mode cannot enable action dispatch or real Jira")
        if self.jira_real_enabled and (
            not self.jira_api_token
            or not self.jira_external_writes_authorized
            or not self.jira_base_url
            or not self.jira_project_key
        ):
            raise ValueError(
                "real Jira requires a credential and explicit external-write authority"
            )
        if self.jira_external_writes_authorized and self.environment != "local":
            raise ValueError(
                "external Jira writes are restricted to an explicitly authorized local profile"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
