from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.knowledge_base.schemas import KnowledgeBaseSchema
from src.modules.toolsets.schemas import ToolsetSchema



class AgentSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    prompt: str
    contextualize_system_prompt: str
    enum_model: str
    max_response_tokens: int
    temperature: float
    history_message_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    knowledge_bases: List[KnowledgeBaseSchema] = Field(default_factory=list)
    toolsets: List[ToolsetSchema] = Field(default_factory=list)

class AgentKnowledgeBaseAssociationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: UUID
    knowledge_base_id: UUID
    created_at: datetime
    agent: Optional[AgentSchema] = None
    knowledge_base: Optional[KnowledgeBaseSchema] = None


class AgentToolsetAssociationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: UUID
    toolset_id: UUID
    created_at: datetime
    agent: Optional[AgentSchema] = None
    toolset: Optional[ToolsetSchema] = None

