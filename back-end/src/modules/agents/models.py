import uuid
import enum

from sqlalchemy import ARRAY, Integer, String, ForeignKey, Boolean,  DateTime, func, Index, Text, Table, Float
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.database.session_manager import Base
 

class AgentKnowledgeBaseAssociation(Base):
    __tablename__ = 'agent_knowledge_base_association'

    agent_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('agent.id'), primary_key=True)
    knowledge_base_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('knowledge_base.id'), primary_key=True)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())

    def __repr__(self):
        return f"AgentKnowledgeBaseAssociation(agent_id={self.agent_data_source_id}, knowledge_base_id={self.knowledge_base_id})"

class AgentToolsetAssociation(Base):
    __tablename__ = 'agent_toolset_association'

    agent_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('agent.id'), primary_key=True)
    toolset_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('toolset.id'), primary_key=True)

    created_at = mapped_column(DateTime, nullable=False, default=func.now())

class Agent(Base):
    __tablename__ = 'agent'

    id = mapped_column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)
    name = mapped_column(String(128), nullable=False)
    description = mapped_column(Text, nullable=True)
    color = mapped_column(String(16), nullable=True)
    prompt = mapped_column(Text, nullable=False)
    contextualize_system_prompt = mapped_column(Text, nullable=False)

    enum_model = mapped_column(
        String(64), nullable=False, default="chatgpt_3_5_turbo")

    max_response_tokens = mapped_column(Integer, default=16000, nullable=False)
    temperature = mapped_column(Float, default=1.0, nullable=False)
    history_message_count = mapped_column(Integer, default=10, nullable=False)

    is_active = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __str__(self) -> str:
        return self.name

