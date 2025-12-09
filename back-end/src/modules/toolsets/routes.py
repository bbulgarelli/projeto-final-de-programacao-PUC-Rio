from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import DBSessionDep
from src.modules.agents.models import Agent
from src.modules.toolsets.MCPManager import MCPManager
from src.modules.toolsets.enums.enums import ToolTypeEnum, ToolsetTypeEnum
from src.modules.toolsets.repositories.ToolRepository import (
    ToolRepository,
    create_tool_repository,
    get_tool_repository,
)
from src.modules.toolsets.repositories.ToolsetRepository import (
    ToolsetRepository,
    create_toolset_repository,
    get_toolset_repository,
)
from .routes_schemas import (
    CreateTool,
    CreateToolset,
    ToolResponse,
    ToolsetListResponse,
    ToolsetResponse,
    UpdateTool,
    UpdateToolset,
)

toolset_router = APIRouter(tags=["Toolset Management"])


async def _ensure_agent_exists(session: AsyncSession, agent_id: UUID) -> None:
    stmt = select(Agent.id).where(Agent.id == agent_id, Agent.is_active == True)
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


@toolset_router.post(
    "/toolsets",
    status_code=status.HTTP_201_CREATED,
    response_model=ToolsetResponse,
)
async def create_toolset(data: CreateToolset, session: DBSessionDep):
    """Create a new toolset and optionally set up MCP integration or nested tools."""
    toolset_type = data.enum or ToolsetTypeEnum.CUSTOM
    toolset_repo = await create_toolset_repository(
        session=session,
        name=data.name,
        description=data.description,
        toolset_type=toolset_type,
        mcp_server_url=data.mcp_server_url,
        mcp_server_auth_header=data.mcp_server_auth_header,
    )

    if toolset_type == ToolsetTypeEnum.MCP_SERVER:
        manager = MCPManager(
            toolset_repo=toolset_repo,
            mcp_server_url=data.mcp_server_url,
            mcp_server_auth_header=data.mcp_server_auth_header,
        )
        await manager.setup_mcp(session)

    if data.tools:
        for tool in data.tools:
            tool_type = tool.enum
            if tool_type is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tool_type is required.")
            if tool_type == ToolTypeEnum.AGENT and tool.target_agent_id:
                await _ensure_agent_exists(session, tool.target_agent_id)
            await create_tool_repository(
                session=session,
                name=tool.name,
                description=tool.description,
                tool_type=tool_type,
                webhook_url=tool.webhook_url,
                webhook_auth_header=tool.webhook_auth_header,
                webhook_query_params_schema=tool.webhook_query_params_schema,
                webhook_path_params_schema=tool.webhook_path_params_schema,
                webhook_body_params_schema=tool.webhook_body_params_schema,
                webhook_http_method=tool.webhook_http_method,
                mcp_title=None,
                input_schema=None,
                output_schema=None,
                target_agent_id=tool.target_agent_id,
                toolset_id=toolset_repo.toolset.id if toolset_repo.toolset else None,
            )

    await toolset_repo.load(toolset_repo.toolset.id)
    await session.commit()
    response = toolset_repo.get_toolset().model_dump()
    return response


@toolset_router.get(
    "/toolsets",
    response_model=ToolsetListResponse,
)
async def list_toolsets(
    session: DBSessionDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List toolsets with pagination metadata."""
    toolsets = await ToolsetRepository.paginate_toolsets(session, page_number, page_size)
    total = await ToolsetRepository.count_toolsets(session)
    return ToolsetListResponse(
        total_toolsets=total,
        toolsets=[ts.model_dump() for ts in toolsets],
    )


@toolset_router.get(
    "/toolsets/{toolset_id}",
    response_model=ToolsetResponse,
)
async def get_toolset(toolset_id: UUID, session: DBSessionDep):
    """Retrieve a toolset by its identifier."""
    repo = await get_toolset_repository(session, toolset_id)
    return repo.get_toolset()


@toolset_router.patch(
    "/toolsets/{toolset_id}",
    response_model=ToolsetResponse,
)
async def update_toolset(toolset_id: UUID, data: UpdateToolset, session: DBSessionDep):
    """Update metadata or type information for an existing toolset."""
    repo = await get_toolset_repository(session, toolset_id)
    await repo.update(
        name=data.name,
        description=data.description,
        toolset_type=data.enum,
        mcp_server_url=data.mcp_server_url,
        mcp_server_auth_header=data.mcp_server_auth_header,
    )
    await session.commit()
    return repo.get_toolset()


@toolset_router.delete(
    "/toolsets/{toolset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_toolset(toolset_id: UUID, session: DBSessionDep):
    """Delete a toolset and its associated tools."""
    repo = await get_toolset_repository(session, toolset_id)
    await repo.delete()
    await session.commit()


@toolset_router.get(
    "/toolsets/{toolset_id}/mcp-server-auth-header",
)
async def get_mcp_server_auth_header(toolset_id: UUID, session: DBSessionDep):
    """Return the MCP server auth header for the specified toolset, if present."""
    repo = await get_toolset_repository(session, toolset_id)
    return repo.toolset.mcp_server_auth_header if repo.toolset else None


@toolset_router.post(
    "/toolsets/{toolset_id}/tools",
    status_code=status.HTTP_201_CREATED,
    response_model=ToolResponse,
    tags=["Tool Management"],
)
async def create_tool(toolset_id: UUID, data: CreateTool, session: DBSessionDep):
    """Create a new tool inside a custom toolset."""
    toolset_repo = await get_toolset_repository(session, toolset_id)
    toolset_schema = toolset_repo.get_toolset()
    if toolset_schema.toolset_type != ToolsetTypeEnum.CUSTOM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tools can only be added to CUSTOM toolsets.")

    tool_type = data.enum
    if tool_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tool_type is required.")

    if tool_type == ToolTypeEnum.AGENT and data.target_agent_id:
        await _ensure_agent_exists(session, data.target_agent_id)

    tool_repo = await create_tool_repository(
        session=session,
        name=data.name,
        description=data.description,
        tool_type=tool_type,
        webhook_url=data.webhook_url,
        webhook_auth_header=data.webhook_auth_header,
        webhook_query_params_schema=data.webhook_query_params_schema,
        webhook_path_params_schema=data.webhook_path_params_schema,
        webhook_body_params_schema=data.webhook_body_params_schema,
        webhook_http_method=data.webhook_http_method,
        mcp_title=data.mcp_title,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        target_agent_id=data.target_agent_id,
        toolset_id=toolset_id,
    )
    await session.commit()
    return tool_repo.get_tool()


@toolset_router.get(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    tags=["Tool Management"],
)
async def get_tool(tool_id: UUID, session: DBSessionDep):
    """Retrieve a tool by its identifier."""
    repo = await get_tool_repository(session, tool_id)
    return repo.get_tool()


@toolset_router.patch(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    tags=["Tool Management"],
)
async def update_tool(tool_id: UUID, data: UpdateTool, session: DBSessionDep):
    """Update tool metadata or configuration within a custom toolset."""
    tool_repo = await get_tool_repository(session, tool_id)
    if not tool_repo.tool or not tool_repo.tool.toolset_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool is not linked to a toolset.")

    toolset_repo = await get_toolset_repository(session, tool_repo.tool.toolset_id)
    if toolset_repo.get_toolset().toolset_type != ToolsetTypeEnum.CUSTOM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tools can only be updated for CUSTOM toolsets.")

    new_tool_type = data.enum
    if new_tool_type == ToolTypeEnum.AGENT and data.target_agent_id:
        await _ensure_agent_exists(session, data.target_agent_id)

    await tool_repo.update(
        name=data.name,
        description=data.description,
        tool_type=new_tool_type,
        webhook_url=data.webhook_url,
        webhook_auth_header=data.webhook_auth_header,
        webhook_query_params_schema=data.webhook_query_params_schema,
        webhook_path_params_schema=data.webhook_path_params_schema,
        webhook_body_params_schema=data.webhook_body_params_schema,
        webhook_http_method=data.webhook_http_method,
        mcp_title=data.mcp_title,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        target_agent_id=data.target_agent_id,
    )
    await session.commit()
    return tool_repo.get_tool()


@toolset_router.delete(
    "/tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tool Management"],
)
async def delete_tool(tool_id: UUID, session: DBSessionDep):
    """Delete a tool from its toolset."""
    repo = await get_tool_repository(session, tool_id)
    await repo.delete()
    await session.commit()


@toolset_router.get(
    "/tools/{tool_id}/webhook-auth-header",
    tags=["Tool Management"],
)
async def get_webhook_auth_header(tool_id: UUID, session: DBSessionDep):
    """Return the webhook authorization headers for the specified tool, if set."""
    repo = await get_tool_repository(session, tool_id)
    return repo.tool.webhook_auth_header if repo.tool else None
