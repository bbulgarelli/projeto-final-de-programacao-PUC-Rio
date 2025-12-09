from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.modules.knowledge_base.routes_schemas import KnowledgeBaseResponse
from src.modules.toolsets.routes_schemas import ToolsetResponse


class CreateAgent(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Display name of the agent.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Optional summary that describes the agent role.",
    )
    color: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Optional hex or CSS color code used for UI representation.",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        description="System prompt defining the agent primary behavior.",
    )
    contextualize_system_prompt: str = Field(
        ...,
        description="Supplementary prompt used to contextualize responses.",
    )
    enum_model: Optional[str] = Field(
        default="chatgpt_3_5_turbo",
        max_length=64,
        description="Model identifier the agent should use when responding.",
    )
    max_response_tokens: Optional[int] = Field(
        default=16000,
        ge=1,
        description="Maximum number of tokens the agent can generate in a reply.",
    )
    temperature: Optional[float] = Field(
        default=1.0,
        ge=0,
        le=2,
        description="Sampling temperature controlling randomness of responses.",
    )
    history_message_count: Optional[int] = Field(
        default=10,
        ge=0,
        description="Number of previous messages to include as context.",
    )
    knowledge_base_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Optional list of knowledge base identifiers linked to the agent.",
    )
    toolset_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Optional list of toolset identifiers the agent can use.",
    )

    @field_validator("knowledge_base_ids", "toolset_ids")
    @classmethod
    def validate_unique_ids(cls, value: Optional[List[UUID]]):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("IDs must be unique")
        return value


class UpdateAgent(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Updated display name of the agent.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Updated summary that describes the agent role.",
    )
    color: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Updated hex or CSS color code used for UI representation.",
    )
    prompt: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated system prompt defining the agent behavior.",
    )
    contextualize_system_prompt: Optional[str] = Field(
        default=None,
        description="Updated supplementary prompt used to contextualize responses.",
    )
    enum_model: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Updated model identifier the agent should use when responding.",
    )
    max_response_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Updated maximum number of tokens the agent can generate in a reply.",
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0,
        le=2,
        description="Updated sampling temperature controlling randomness of responses.",
    )
    history_message_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated number of previous messages to include as context.",
    )
    knowledge_base_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Updated list of knowledge base identifiers linked to the agent.",
    )
    toolset_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Updated list of toolset identifiers the agent can use.",
    )

    @field_validator("knowledge_base_ids", "toolset_ids")
    @classmethod
    def validate_unique_ids(cls, value: Optional[List[UUID]]):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("IDs must be unique")
        return value


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the agent.")
    name: str = Field(..., min_length=1, max_length=128, description="Display name of the agent.")
    description: Optional[str] = Field(
        default=None,
        description="Summary that describes the agent role.",
    )
    color: Optional[str] = Field(
        default=None,
        description="Hex or CSS color code used for UI representation.",
    )
    prompt: str = Field(..., min_length=1, description="Primary system prompt for the agent.")
    contextualize_system_prompt: str = Field(
        ...,
        description="Supplementary prompt used to contextualize responses.",
    )
    enum_model: str = Field(
        ...,
        description="Model identifier the agent uses when responding.",
    )
    max_response_tokens: int = Field(
        ...,
        description="Maximum number of tokens the agent can generate in a reply.",
    )
    temperature: float = Field(
        ...,
        description="Sampling temperature controlling randomness of responses.",
    )
    history_message_count: int = Field(
        ...,
        description="Number of previous messages included as context.",
    )
    is_active: bool = Field(..., description="Indicates whether the agent is active.")
    created_at: datetime = Field(..., description="Timestamp when the agent was created.")
    updated_at: datetime = Field(..., description="Timestamp when the agent was last updated.")
    knowledge_bases: List[KnowledgeBaseResponse] = Field(
        default_factory=list,
        description="Knowledge bases linked to this agent.",
    )
    toolsets: List[ToolsetResponse] = Field(
        default_factory=list,
        description="Toolsets the agent can interact with.",
    )


class AgentListResponse(BaseModel):
    total_agents: int = Field(..., ge=0, description="Total number of agents available.")
    agents: List[AgentResponse] = Field(
        default_factory=list,
        description="Paginated list of agents.",
    )

