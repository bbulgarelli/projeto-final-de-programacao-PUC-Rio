from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.modules.toolsets.enums.enums import ToolTypeEnum, ToolsetTypeEnum
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ToolSchema(BaseModel):
    id: UUID
    tool_type: ToolTypeEnum
    name: str
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_auth_header: Optional[dict] = None
    webhook_query_params_schema: Optional[dict] = None
    webhook_path_params_schema: Optional[dict] = None
    webhook_body_params_schema: Optional[dict] = None
    webhook_http_method: Optional[str] = None
    mcp_title: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    nplabs_tool_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    target_agent_id: Optional[UUID] = None
    toolset_id: Optional[UUID] = None

    @field_serializer("tool_type")
    def serialize_tool_type(self, value: ToolTypeEnum) -> str:
        return str(value.name)


class ToolsetSchema(BaseModel):
    id: UUID
    toolset_type: ToolsetTypeEnum
    enum_toolset_type: str
    name: str
    description: Optional[str] = None
    mcp_server_url: Optional[str] = None
    mcp_server_auth_header: Optional[dict] = None
    enum_np_toolset: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tools: List[ToolSchema] = Field(default_factory=list)

    @field_serializer("toolset_type")
    def serialize_toolset_type(self, value: ToolsetTypeEnum) -> str:
        return str(value.name)

ToolSchema.model_rebuild()
ToolsetSchema.model_rebuild()
 