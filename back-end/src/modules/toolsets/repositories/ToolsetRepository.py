from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.toolsets.enums.enums import ToolsetTypeEnum

from ..models import Toolset, Tool
from ..schemas import ToolSchema, ToolsetSchema
from .ToolRepository import ToolRepository


async def get_toolset_repository(session: AsyncSession, toolset_id: UUID) -> "ToolsetRepository":
    """
    Factory to create a ToolsetRepository instance and load an existing toolset.

    Args:
        session (AsyncSession): The database session.
        toolset_id (UUID): The unique identifier of the toolset.

    Returns:
        ToolsetRepository: An instance of the repository with the loaded toolset.
    """
    repo = ToolsetRepository(session)
    await repo.load(toolset_id)
    return repo


async def create_toolset_repository(
    session: AsyncSession,
    *,
    name: str,
    description: Optional[str],
    toolset_type: ToolsetTypeEnum,
    mcp_server_url: Optional[str],
    mcp_server_auth_header: Optional[dict],
) -> "ToolsetRepository":
    """
    Factory to create a ToolsetRepository instance and a new toolset.

    Args:
        session (AsyncSession): The database session.
        name (str): Name of the toolset.
        description (Optional[str]): Description of the toolset.
        toolset_type (ToolsetTypeEnum): Type of the toolset.
        mcp_server_url (Optional[str]): URL for MCP server if applicable.
        mcp_server_auth_header (Optional[dict]): Auth headers for MCP server.

    Returns:
        ToolsetRepository: An instance of the repository with the created toolset.
    """
    repo = ToolsetRepository(session)
    await repo.create(
        name=name,
        description=description,
        toolset_type=toolset_type,
        mcp_server_url=mcp_server_url,
        mcp_server_auth_header=mcp_server_auth_header,
    )
    return repo


class ToolsetRepository:
    """
    Repository for managing Toolset entities.

    Handles CRUD operations for toolsets and loading of associated tools.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.toolset: Optional[Toolset] = None
        self._tools: List[Tool] = []

    async def load(self, toolset_id: UUID):
        stmt = select(Toolset).where(Toolset.id == toolset_id, Toolset.is_active == True)
        result = await self.session.execute(stmt)
        toolset = result.scalar_one_or_none()
        if not toolset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Toolset not found")
        self.toolset = toolset
        tool_map = await self._fetch_tools_map(self.session, [toolset.id])
        self._tools = tool_map.get(toolset.id, [])
        self.toolset_schema = self.create_toolset_schema(self.toolset, self._tools)
        return self

    async def create(
        self,
        *,
        name: str,
        description: Optional[str],
        toolset_type: ToolsetTypeEnum,
        mcp_server_url: Optional[str],
        mcp_server_auth_header: Optional[dict],
    ):
        toolset = Toolset(
            name=name,
            description=description,
            enum_toolset_type=toolset_type.name,
            mcp_server_url=mcp_server_url,
            mcp_server_auth_header=mcp_server_auth_header,
        )
        self.session.add(toolset)
        await self.session.flush()
        await self.session.refresh(toolset)
        self.toolset = toolset
        self._tools = []
        self.toolset_schema = self.create_toolset_schema(self.toolset, self._tools)
        return self

    async def update(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        toolset_type: Optional[ToolsetTypeEnum] = None,
        mcp_server_url: Optional[str] = None,
        mcp_server_auth_header: Optional[dict] = None,
    ):
        if not self.toolset:
            raise RuntimeError("Toolset repository is not initialized.")

        if name is not None:
            self.toolset.name = name
        if description is not None:
            self.toolset.description = description
        if toolset_type is not None:
            self.toolset.enum_toolset_type = toolset_type.name
        if mcp_server_url is not None:
            self.toolset.mcp_server_url = mcp_server_url
        if mcp_server_auth_header is not None:
            self.toolset.mcp_server_auth_header = mcp_server_auth_header

        await self.session.flush()
        await self.session.refresh(self.toolset)
        self.toolset_schema = self.create_toolset_schema(self.toolset, self._tools)
        return self

    async def delete(self):
        if not self.toolset:
            raise RuntimeError("Toolset repository is not initialized.")
        self.toolset.is_active = False
        await self.session.flush()
        await self.session.refresh(self.toolset)
        return self

    def get_toolset(self) -> ToolsetSchema:
        return self.toolset_schema

    @staticmethod
    async def paginate_toolsets(
        session: AsyncSession, page_number: int, page_size: int
    ) -> List[ToolsetSchema]:
        offset = (page_number - 1) * page_size
        stmt = (
            select(Toolset)
            .where(Toolset.is_active == True)
            .offset(offset)
            .limit(page_size)
            .order_by(Toolset.created_at.desc())
        )
        result = await session.execute(stmt)
        toolsets = result.scalars().all()
        tool_map = await ToolsetRepository._fetch_tools_map(session, [ts.id for ts in toolsets])
        return [
            ToolsetRepository.create_toolset_schema(toolset, tool_map.get(toolset.id, []))
            for toolset in toolsets
        ]

    @staticmethod
    async def count_toolsets(session: AsyncSession) -> int:
        stmt = select(func.count(Toolset.id)).where(Toolset.is_active == True)
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def create_toolset_schema(
        toolset: Toolset, tools: Optional[List[Tool]] = None
    ) -> ToolsetSchema:
        serialized_tools: List[ToolSchema] = []
        if tools:
            serialized_tools = [
                ToolRepository.create_tool_schema(tool)
                for tool in tools
                if tool.is_active
            ]
        return ToolsetSchema(
            id=toolset.id,
            toolset_type=ToolsetTypeEnum[toolset.enum_toolset_type],
            enum_toolset_type=toolset.enum_toolset_type,
            name=toolset.name,
            description=toolset.description,
            mcp_server_url=toolset.mcp_server_url,
            mcp_server_auth_header=toolset.mcp_server_auth_header,
            enum_np_toolset=toolset.enum_np_toolset,
            is_active=toolset.is_active,
            created_at=toolset.created_at,
            updated_at=toolset.updated_at,
            tools=serialized_tools,
        )

    @staticmethod
    async def _fetch_tools_map(session: AsyncSession, toolset_ids: List[UUID]) -> Dict[UUID, List[Tool]]:
        if not toolset_ids:
            return {}
        stmt = select(Tool).where(
            Tool.toolset_id.in_(toolset_ids),
            Tool.is_active == True,
        )
        result = await session.execute(stmt)
        tools = result.scalars().all()
        tool_map: Dict[UUID, List[Tool]] = {}
        for tool in tools:
            tool_map.setdefault(tool.toolset_id, []).append(tool)
        return tool_map
