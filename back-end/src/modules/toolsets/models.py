import uuid

from sqlalchemy import Integer, String, ForeignKey, Boolean,  DateTime, func, Index, Text
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.database.session_manager import Base

class Toolset(Base):
    __tablename__ = 'toolset'
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enum_toolset_type = mapped_column(String, nullable=False) # Literal: "NP Toolset", "MCP Server", "Custom", "NP Custom Toolset"
    name = mapped_column(String, nullable=False)
    description = mapped_column(Text, nullable=True)

    mcp_server_url = mapped_column(String, nullable=True)
    mcp_server_auth_header = mapped_column(JSONB, nullable=True)

    enum_np_toolset = mapped_column(String, nullable=True)

    is_active = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __str__(self):
        return self.name


class Tool(Base):
    __tablename__ = 'tool'
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enum_tool_type = mapped_column(String, nullable=False) # Literal: "Webhook", "Agent", "MCP"
    name = mapped_column(String, nullable=False)
    description = mapped_column(Text, nullable=True)

    webhook_url = mapped_column(String, nullable=True)
    webhook_auth_header = mapped_column(JSONB, nullable=True)
    webhook_query_params_schema = mapped_column(JSONB, nullable=True)
    webhook_path_params_schema = mapped_column(JSONB, nullable=True)
    webhook_body_params_schema = mapped_column(JSONB, nullable=True)
    webhook_http_method = mapped_column(String, nullable=True) # Literal: "GET", "POST", "PUT", "PATCH", "DELETE"

    #MCP
    mcp_title = mapped_column(String, nullable=True)
    input_schema = mapped_column(JSONB, nullable=True)
    output_schema = mapped_column(JSONB, nullable=True)
    
    nplabs_tool_id = mapped_column(String, nullable=True)
    
    is_active = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    target_agent_id = mapped_column(UUID(as_uuid=True), ForeignKey('agent.id'), nullable=True)
    toolset_id = mapped_column(UUID(as_uuid=True), ForeignKey('toolset.id'), nullable=True)

    toolset = relationship("Toolset")

    def __str__(self):
        return self.name


# Database indexes for performance
Index('idx_tool_toolset_id', Tool.toolset_id)
