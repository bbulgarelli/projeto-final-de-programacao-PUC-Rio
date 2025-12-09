from typing import Any, Dict, Optional
import json

from fastapi import HTTPException
from pydantic_ai.mcp import MCPServer, MCPServerStreamableHTTP, MCPServerSSE
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.toolsets.enums.enums import ToolTypeEnum
from src.modules.toolsets.repositories.ToolRepository import create_tool_repository
from src.modules.toolsets.repositories.ToolsetRepository import ToolsetRepository


class MCPManager:
    def __init__(
        self,
        toolset_repo: ToolsetRepository,
        mcp_server_url: str,
        mcp_server_auth_header: Optional[Any],
    ):
        self.toolset_repo = toolset_repo
        self.mcp_server_url = mcp_server_url
        self.mcp_server_auth_header = mcp_server_auth_header

    async def setup_mcp(self, session: AsyncSession):
        headers: Optional[Dict[str, str]] = None
        if self.mcp_server_auth_header:
            if isinstance(self.mcp_server_auth_header, dict):
                headers = self.mcp_server_auth_header
            elif isinstance(self.mcp_server_auth_header, str):
                try:
                    headers = json.loads(self.mcp_server_auth_header)
                except json.JSONDecodeError:
                    headers = None

        mcp_tools = None
        last_exception: Optional[Exception] = None

        for server_type in [MCPServerStreamableHTTP, MCPServerSSE]:
            server: MCPServer = server_type(url=self.mcp_server_url)
            try:
                mcp_tools = await server.list_tools()
                break
            except Exception as exc:
                last_exception = exc
        else:
            raise HTTPException(status_code=400, detail=f"Error connecting to MCP server: {last_exception}")

        if not self.toolset_repo.toolset:
            raise HTTPException(status_code=400, detail="Toolset repository is not initialized.")

        for tool in mcp_tools or []:
            await create_tool_repository(
                session=session,
                name=tool.name,
                description=tool.description,
                tool_type=ToolTypeEnum.MCP,
                mcp_title=tool.title,
                input_schema=tool.inputSchema,
                output_schema=tool.outputSchema,
                toolset_id=self.toolset_repo.toolset.id,
            )