from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
    PrivateAttr,
)
from pydantic_core import ErrorDetails

from src.modules.toolsets.enums.enums import ToolTypeEnum, ToolsetTypeEnum


def _validate_tool_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = [enum.name for enum in ToolTypeEnum.get_visible_types()]
    if value not in allowed:
        allowed_str = ", ".join(allowed)
        raise ValueError(f"tool_type must be one of: {allowed_str}")
    return value


def _validate_toolset_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = [enum.name for enum in ToolsetTypeEnum.get_visible_types()]
    if value not in allowed:
        allowed_str = ", ".join(allowed)
        raise ValueError(f"toolset_type must be one of: {allowed_str}")
    return value


class CreateTool(BaseModel):
    _tool_type_enum: Optional[ToolTypeEnum] = PrivateAttr(default=None)

    tool_type: Optional[str] = Field(
        default=None,
        description=f"Type of tool to create. Allowed values: {ToolTypeEnum.get_field_names()}.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the tool.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description explaining what the tool does.",
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="Target URL invoked when the tool type is WEBHOOK.",
    )
    webhook_auth_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="Headers to include when invoking webhook tools.",
    )
    webhook_query_params_schema: Optional[Dict] = Field(
        default=None,
        description="JSON schema describing accepted query parameters for webhook tools.",
    )
    webhook_path_params_schema: Optional[Dict] = Field(
        default=None,
        description="JSON schema describing accepted path parameters for webhook tools.",
    )
    webhook_body_params_schema: Optional[Dict] = Field(
        default=None,
        description="JSON schema describing accepted body parameters for webhook tools.",
    )
    webhook_http_method: Optional[str] = Field(
        default=None,
        description="HTTP method to use for webhook tools.",
        pattern="^(GET|POST|PUT|PATCH|DELETE)$",
    )
    target_agent_id: Optional[UUID] = Field(
        default=None,
        description="Agent identifier required when the tool type is AGENT.",
    )
    mcp_title: Optional[str] = Field(
        default=None,
        description="Title used when the tool is sourced from an MCP server.",
    )
    input_schema: Optional[Dict] = Field(
        default=None,
        description="JSON schema describing the expected tool input.",
    )
    output_schema: Optional[Dict] = Field(
        default=None,
        description="JSON schema describing the tool output.",
    )

    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_tool_type(value)

    @model_validator(mode="after")
    def validate_by_type(self):
        if self.tool_type is not None:
            self._tool_type_enum = ToolTypeEnum[self.tool_type]

        if self._tool_type_enum == ToolTypeEnum.WEBHOOK and not self.webhook_url:
            raise ValidationError.from_exception_data(
                "CreateTool",
                [
                    ErrorDetails(
                        type="missing",
                        loc=("webhook_url",),
                        msg="webhook_url is required for WEBHOOK tools.",
                        input=self.webhook_url,
                    )
                ],
            )
        if self._tool_type_enum == ToolTypeEnum.AGENT and not self.target_agent_id:
            raise ValidationError.from_exception_data(
                "CreateTool",
                [
                    ErrorDetails(
                        type="missing",
                        loc=("target_agent_id",),
                        msg="target_agent_id is required for AGENT tools.",
                        input=self.target_agent_id,
                    )
                ],
            )
        return self

    @property
    def enum(self) -> Optional[ToolTypeEnum]:
        return self._tool_type_enum


class UpdateTool(BaseModel):
    _tool_type_enum: Optional[ToolTypeEnum] = PrivateAttr(default=None)

    tool_type: Optional[str] = Field(
        default=None,
        description=f"Updated tool type. Allowed values: {ToolTypeEnum.get_field_names()}.",
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated display name of the tool.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated description of the tool.",
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="Updated target URL invoked when the tool type is WEBHOOK.",
    )
    webhook_auth_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="Updated headers to include when invoking webhook tools.",
    )
    webhook_query_params_schema: Optional[Dict] = Field(
        default=None,
        description="Updated JSON schema describing accepted query parameters for webhook tools.",
    )
    webhook_path_params_schema: Optional[Dict] = Field(
        default=None,
        description="Updated JSON schema describing accepted path parameters for webhook tools.",
    )
    webhook_body_params_schema: Optional[Dict] = Field(
        default=None,
        description="Updated JSON schema describing accepted body parameters for webhook tools.",
    )
    webhook_http_method: Optional[str] = Field(
        default=None,
        description="Updated HTTP method to use for webhook tools.",
        pattern="^(GET|POST|PUT|PATCH|DELETE)$",
    )
    target_agent_id: Optional[UUID] = Field(
        default=None,
        description="Updated agent identifier when the tool type is AGENT.",
    )
    mcp_title: Optional[str] = Field(
        default=None,
        description="Updated MCP server title if applicable.",
    )
    input_schema: Optional[Dict] = Field(
        default=None,
        description="Updated JSON schema describing the expected tool input.",
    )
    output_schema: Optional[Dict] = Field(
        default=None,
        description="Updated JSON schema describing the tool output.",
    )

    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_tool_type(value)

    @model_validator(mode="after")
    def validate_by_type(self):
        if self.tool_type is not None:
            self._tool_type_enum = ToolTypeEnum[self.tool_type]

        if self._tool_type_enum == ToolTypeEnum.WEBHOOK and self.webhook_url is None:
            raise ValidationError.from_exception_data(
                "UpdateTool",
                [
                    ErrorDetails(
                        type="missing",
                        loc=("webhook_url",),
                        msg="webhook_url is required for WEBHOOK tools.",
                        input=self.webhook_url,
                    )
                ],
            )
        if self._tool_type_enum == ToolTypeEnum.AGENT and self.target_agent_id is None:
            raise ValidationError.from_exception_data(
                "UpdateTool",
                [
                    ErrorDetails(
                        type="missing",
                        loc=("target_agent_id",),
                        msg="target_agent_id is required for AGENT tools.",
                        input=self.target_agent_id,
                    )
                ],
            )
        return self

    @property
    def enum(self) -> Optional[ToolTypeEnum]:
        return self._tool_type_enum


class ToolResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the tool.")
    name: str = Field(..., min_length=1, max_length=255, description="Display name of the tool.")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Description explaining what the tool does.",
    )
    tool_type: str = Field(..., description="Type of the tool (e.g., WEBHOOK, AGENT).")
    webhook_url: Optional[str] = Field(
        default=None,
        description="Target URL invoked when the tool type is WEBHOOK.",
    )
    webhook_auth_header: Optional[dict] = Field(
        default=None,
        description="Headers included when invoking webhook tools.",
    )
    webhook_query_params_schema: Optional[dict] = Field(
        default=None,
        description="Schema describing accepted query parameters for webhook tools.",
    )
    webhook_path_params_schema: Optional[dict] = Field(
        default=None,
        description="Schema describing accepted path parameters for webhook tools.",
    )
    webhook_body_params_schema: Optional[dict] = Field(
        default=None,
        description="Schema describing accepted body parameters for webhook tools.",
    )
    webhook_http_method: Optional[str] = Field(
        default=None,
        description="HTTP method used for webhook tools.",
    )
    mcp_title: Optional[str] = Field(
        default=None,
        description="Title used when the tool originates from an MCP server.",
    )
    input_schema: Optional[dict] = Field(
        default=None,
        description="Schema describing the expected tool input.",
    )
    output_schema: Optional[dict] = Field(
        default=None,
        description="Schema describing the tool output.",
    )
    target_agent_id: Optional[UUID] = Field(
        default=None,
        description="Identifier of the target agent when the tool type is AGENT.",
    )
    toolset_id: Optional[UUID] = Field(
        default=None,
        description="Identifier of the toolset this tool belongs to.",
    )
    is_active: bool = Field(..., description="Indicates whether the tool is active.")
    created_at: datetime = Field(..., description="Timestamp when the tool was created.")
    updated_at: datetime = Field(..., description="Timestamp when the tool was last updated.")


class CreateToolset(BaseModel):
    _toolset_type_enum: Optional[ToolsetTypeEnum] = PrivateAttr(default=None)

    toolset_type: Optional[str] = Field(
        default=None,
        description=f"Type of the toolset. Allowed values: {ToolsetTypeEnum.get_field_names()}.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the toolset.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description explaining what the toolset contains.",
    )
    mcp_server_url: Optional[str] = Field(
        default=None,
        description="Server URL required when the toolset type is MCP_SERVER.",
    )
    mcp_server_auth_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="Authorization headers used to communicate with the MCP server.",
    )
    tools: Optional[List[CreateTool]] = Field(
        default=None,
        description="Optional list of tools to be created alongside the toolset.",
    )

    @field_validator("toolset_type")
    @classmethod
    def validate_toolset_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_toolset_type(value)

    @model_validator(mode="after")
    def validate_schema(self):
        if self.toolset_type is not None:
            self._toolset_type_enum = ToolsetTypeEnum[self.toolset_type]

        if self._toolset_type_enum == ToolsetTypeEnum.MCP_SERVER:
            if not self.mcp_server_url:
                raise ValidationError.from_exception_data(
                    "CreateToolset",
                    [
                        ErrorDetails(
                            type="missing",
                            loc=("mcp_server_url",),
                            msg="mcp_server_url is required for MCP_SERVER toolsets.",
                            input=self.mcp_server_url,
                        )
                    ],
                )
            if self.tools:
                raise ValidationError.from_exception_data(
                    "CreateToolset",
                    [
                        ErrorDetails(
                            type="value_error",
                            loc=("tools",),
                            msg="Tools cannot be provided for MCP_SERVER toolsets.",
                            input=[tool.name for tool in self.tools],
                        )
                    ],
                )
        return self

    @property
    def enum(self) -> Optional[ToolsetTypeEnum]:
        return self._toolset_type_enum


class UpdateToolset(BaseModel):
    _toolset_type_enum: Optional[ToolsetTypeEnum] = PrivateAttr(default=None)

    toolset_type: Optional[str] = Field(
        default=None,
        description=f"Updated toolset type. Allowed values: {ToolsetTypeEnum.get_field_names()}.",
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated display name of the toolset.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated description explaining the toolset content.",
    )
    mcp_server_url: Optional[str] = Field(
        default=None,
        description="Updated server URL required when the toolset type is MCP_SERVER.",
    )
    mcp_server_auth_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="Updated authorization headers for the MCP server.",
    )

    @field_validator("toolset_type")
    @classmethod
    def validate_toolset_type(cls, value: Optional[str]) -> Optional[str]:
        return _validate_toolset_type(value)

    @model_validator(mode="after")
    def validate_schema(self):
        if self.toolset_type is not None:
            self._toolset_type_enum = ToolsetTypeEnum[self.toolset_type]

        if self._toolset_type_enum == ToolsetTypeEnum.MCP_SERVER and not self.mcp_server_url:
            raise ValidationError.from_exception_data(
                "UpdateToolset",
                [
                    ErrorDetails(
                        type="missing",
                        loc=("mcp_server_url",),
                        msg="mcp_server_url is required for MCP_SERVER toolsets.",
                        input=self.mcp_server_url,
                    )
                ],
            )
        return self

    @property
    def enum(self) -> Optional[ToolsetTypeEnum]:
        return self._toolset_type_enum


class ToolsetResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the toolset.")
    name: str = Field(..., min_length=1, max_length=255, description="Display name of the toolset.")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Description explaining the toolset purpose.",
    )
    toolset_type: str = Field(..., description="Type of the toolset (e.g., CUSTOM, MCP_SERVER).")
    mcp_server_url: Optional[str] = Field(
        default=None,
        description="Server URL used when the toolset type is MCP_SERVER.",
    )
    mcp_server_auth_header: Optional[dict] = Field(
        default=None,
        description="Authorization headers used to communicate with the MCP server.",
    )
    enum_np_toolset: Optional[str] = Field(
        default=None,
        description="Optional third-party identifier for the toolset.",
    )
    is_active: bool = Field(..., description="Indicates whether the toolset is active.")
    created_at: datetime = Field(..., description="Timestamp when the toolset was created.")
    updated_at: datetime = Field(..., description="Timestamp when the toolset was last updated.")
    tools: List[ToolResponse] = Field(
        default_factory=list,
        description="Tools contained within this toolset.",
    )


class ToolsetListResponse(BaseModel):
    total_toolsets: int = Field(..., ge=0, description="Total number of toolsets available.")
    toolsets: List[ToolsetResponse] = Field(
        default_factory=list,
        description="Paginated list of toolsets.",
    )
