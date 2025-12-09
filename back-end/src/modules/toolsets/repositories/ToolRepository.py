from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.toolsets.enums.enums import ToolTypeEnum

from ..models import Tool
from ..schemas import ToolSchema


async def get_tool_repository(session: AsyncSession, tool_id: UUID) -> "ToolRepository":
    """
    Factory to create a ToolRepository instance and load an existing tool.

    Args:
        session (AsyncSession): The database session.
        tool_id (UUID): The unique identifier of the tool.

    Returns:
        ToolRepository: An instance of the repository with the loaded tool.
    """
    repo = ToolRepository(session)
    await repo.load(tool_id)
    return repo


async def create_tool_repository(
    session: AsyncSession,
    *,
    name: str,
    description: Optional[str],
    tool_type: ToolTypeEnum,
    webhook_url: Optional[str] = None,
    webhook_auth_header: Optional[dict] = None,
    webhook_query_params_schema: Optional[dict] = None,
    webhook_path_params_schema: Optional[dict] = None,
    webhook_body_params_schema: Optional[dict] = None,
    webhook_http_method: Optional[str] = None,
    mcp_title: Optional[str] = None,
    input_schema: Optional[dict] = None,
    output_schema: Optional[dict] = None,
    target_agent_id: Optional[UUID] = None,
    toolset_id: Optional[UUID] = None,
) -> "ToolRepository":
    """
    Factory to create a ToolRepository instance and a new tool.

    Args:
        session (AsyncSession): The database session.
        name (str): Name of the tool.
        description (Optional[str]): Description of the tool.
        tool_type (ToolTypeEnum): The type of tool (e.g., webhook, MCP).
        webhook_url (Optional[str], optional): URL for webhook tools.
        webhook_auth_header (Optional[dict], optional): Auth headers for webhook tools.
        webhook_query_params_schema (Optional[dict], optional): Schema for query params.
        webhook_path_params_schema (Optional[dict], optional): Schema for path params.
        webhook_body_params_schema (Optional[dict], optional): Schema for body params.
        webhook_http_method (Optional[str], optional): HTTP method for webhook.
        mcp_title (Optional[str], optional): Title for MCP tools.
        input_schema (Optional[dict], optional): JSON schema for input.
        output_schema (Optional[dict], optional): JSON schema for output.
        target_agent_id (Optional[UUID], optional): ID of target agent if applicable.
        toolset_id (Optional[UUID], optional): ID of the toolset this tool belongs to.

    Returns:
        ToolRepository: An instance of the repository with the created tool.
    """
    repo = ToolRepository(session)
    await repo.create(
        name=name,
        description=description,
        tool_type=tool_type,
        webhook_url=webhook_url,
        webhook_auth_header=webhook_auth_header,
        webhook_query_params_schema=webhook_query_params_schema,
        webhook_path_params_schema=webhook_path_params_schema,
        webhook_body_params_schema=webhook_body_params_schema,
        webhook_http_method=webhook_http_method,
        mcp_title=mcp_title,
        input_schema=input_schema,
        output_schema=output_schema,
        target_agent_id=target_agent_id,
        toolset_id=toolset_id,
    )
    return repo


class ToolRepository:
    """
    Repository for managing Tool entities.

    Handles creation, updates, and retrieval of tools including webhook and MCP configurations.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool: Optional[Tool] = None

    async def load(self, tool_id: UUID):
        stmt = (
            select(Tool)
            .options(selectinload(Tool.toolset))
            .where(Tool.id == tool_id, Tool.is_active == True)
        )
        result = await self.session.execute(stmt)
        tool = result.scalar_one_or_none()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        self.tool = tool
        self.tool_schema = self.create_tool_schema(self.tool)
        return self

    async def create(
        self,
        *,
        name: str,
        description: Optional[str],
        tool_type: ToolTypeEnum,
        webhook_url: Optional[str],
        webhook_auth_header: Optional[dict],
        webhook_query_params_schema: Optional[dict],
        webhook_path_params_schema: Optional[dict],
        webhook_body_params_schema: Optional[dict],
        webhook_http_method: Optional[str],
        mcp_title: Optional[str],
        input_schema: Optional[dict],
        output_schema: Optional[dict],
        target_agent_id: Optional[UUID],
        toolset_id: Optional[UUID],
    ):
        tool = Tool(
            name=name,
            description=description,
            enum_tool_type=tool_type.name,
            webhook_url=webhook_url,
            webhook_auth_header=webhook_auth_header,
            webhook_query_params_schema=webhook_query_params_schema,
            webhook_path_params_schema=webhook_path_params_schema,
            webhook_body_params_schema=webhook_body_params_schema,
            webhook_http_method=webhook_http_method,
            mcp_title=mcp_title,
            input_schema=input_schema,
            output_schema=output_schema,
            target_agent_id=target_agent_id,
            toolset_id=toolset_id,
        )

        self.session.add(tool)
        await self.session.flush()
        await self.session.refresh(tool)
        self.tool = tool
        self.tool_schema = self.create_tool_schema(self.tool)
        return self

    async def update(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tool_type: Optional[ToolTypeEnum] = None,
        webhook_url: Optional[str] = None,
        webhook_auth_header: Optional[dict] = None,
        webhook_query_params_schema: Optional[dict] = None,
        webhook_path_params_schema: Optional[dict] = None,
        webhook_body_params_schema: Optional[dict] = None,
        webhook_http_method: Optional[str] = None,
        mcp_title: Optional[str] = None,
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
        target_agent_id: Optional[UUID] = None,
    ):
        if not self.tool:
            raise RuntimeError("Tool repository is not initialized.")

        if name is not None:
            self.tool.name = name
        if description is not None:
            self.tool.description = description
        if tool_type is not None:
            self.tool.enum_tool_type = tool_type.name
        if webhook_url is not None:
            self.tool.webhook_url = webhook_url
        if webhook_auth_header is not None:
            self.tool.webhook_auth_header = webhook_auth_header
        if webhook_query_params_schema is not None:
            self.tool.webhook_query_params_schema = webhook_query_params_schema
        if webhook_path_params_schema is not None:
            self.tool.webhook_path_params_schema = webhook_path_params_schema
        if webhook_body_params_schema is not None:
            self.tool.webhook_body_params_schema = webhook_body_params_schema
        if webhook_http_method is not None:
            self.tool.webhook_http_method = webhook_http_method
        if mcp_title is not None:
            self.tool.mcp_title = mcp_title
        if input_schema is not None:
            self.tool.input_schema = input_schema
        if output_schema is not None:
            self.tool.output_schema = output_schema
        if target_agent_id is not None:
            self.tool.target_agent_id = target_agent_id

        await self.session.flush()
        await self.session.refresh(self.tool)
        self.tool_schema = self.create_tool_schema(self.tool)
        return self

    async def delete(self):
        if not self.tool:
            raise RuntimeError("Tool repository is not initialized.")
        self.tool.is_active = False
        await self.session.flush()
        await self.session.refresh(self.tool)
        return self

    def get_tool(self) -> ToolSchema:
        return self.tool_schema

    @staticmethod
    def create_tool_schema(tool: Tool) -> ToolSchema:
        return ToolSchema(
            id=tool.id,
            tool_type=ToolTypeEnum[tool.enum_tool_type],
            name=tool.name,
            description=tool.description,
            webhook_url=tool.webhook_url,
            webhook_auth_header=tool.webhook_auth_header,
            webhook_query_params_schema=tool.webhook_query_params_schema,
            webhook_path_params_schema=tool.webhook_path_params_schema,
            webhook_body_params_schema=tool.webhook_body_params_schema,
            webhook_http_method=tool.webhook_http_method,
            mcp_title=tool.mcp_title,
            input_schema=tool.input_schema,
            output_schema=tool.output_schema,
            nplabs_tool_id=tool.nplabs_tool_id,
            is_active=tool.is_active,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
            target_agent_id=tool.target_agent_id,
            toolset_id=tool.toolset_id
        )