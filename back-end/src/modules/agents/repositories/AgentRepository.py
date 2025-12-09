from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.knowledge_base.repositories.KnowledgeBaseRepository import KnowledgeBaseRepository
from src.modules.toolsets.repositories.ToolsetRepository import ToolsetRepository
from src.modules.agents.models import (
    Agent,
    AgentKnowledgeBaseAssociation,
    AgentToolsetAssociation,
)
from src.modules.agents.schemas import AgentSchema
from src.modules.knowledge_base.models import KnowledgeBase
from src.modules.knowledge_base.schemas import KnowledgeBaseSchema
from src.modules.toolsets.models import Toolset
from src.modules.toolsets.schemas import ToolsetSchema


async def get_agent_repository(session: AsyncSession, agent_id: UUID) -> "AgentRepository":
    """
    Factory to create an AgentRepository instance and load an existing agent.

    Args:
        session (AsyncSession): The database session.
        agent_id (UUID): The unique identifier of the agent to load.

    Returns:
        AgentRepository: An instance of the repository with the loaded agent.
    """
    repo = AgentRepository(session)
    await repo.load(agent_id)
    return repo


async def create_agent_repository(
    session: AsyncSession,
    *,
    name: str,
    prompt: str,
    contextualize_system_prompt: str,
    description: Optional[str],
    color: Optional[str],
    enum_model: str,
    max_response_tokens: int,
    temperature: float,
    history_message_count: int,
    knowledge_base_ids: Optional[List[UUID]],
    toolset_ids: Optional[List[UUID]],
) -> "AgentRepository":
    """
    Factory to create an AgentRepository instance and a new agent.

    Args:
        session (AsyncSession): The database session.
        name (str): The name of the agent.
        prompt (str): The system prompt for the agent.
        contextualize_system_prompt (str): Contextualization instructions for the system prompt.
        description (Optional[str]): A brief description of the agent.
        color (Optional[str]): Color identifier for UI representation.
        enum_model (str): The model identifier to use.
        max_response_tokens (int): Maximum tokens for the response.
        temperature (float): Sampling temperature.
        history_message_count (int): Number of history messages to retain.
        knowledge_base_ids (Optional[List[UUID]]): List of associated knowledge base IDs.
        toolset_ids (Optional[List[UUID]]): List of associated toolset IDs.

    Returns:
        AgentRepository: An instance of the repository with the created agent.
    """
    repo = AgentRepository(session)
    await repo.create(
        name=name,
        prompt=prompt,
        contextualize_system_prompt=contextualize_system_prompt,
        description=description,
        color=color,
        enum_model=enum_model,
        max_response_tokens=max_response_tokens,
        temperature=temperature,
        history_message_count=history_message_count,
        knowledge_base_ids=knowledge_base_ids,
        toolset_ids=toolset_ids,
    )
    return repo


class AgentRepository:
    """
    Repository for managing Agent entities and their associations.

    Handles CRUD operations, loading relationships (knowledge bases, toolsets),
    and converting models to schemas.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent: Optional[Agent] = None
        self._knowledge_bases: List[KnowledgeBase] = []
        self._toolsets: List[Toolset] = []

    async def load(self, agent_id: UUID):
        stmt = select(Agent).where(Agent.id == agent_id, Agent.is_active == True)
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        await self._refresh_related(agent)
        self.agent = agent
        self.agent_schema = self._create_agent_schema(self.agent, self._knowledge_bases, self._toolsets)
        return self

    async def create(
        self,
        *,
        name: str,
        prompt: str,
        contextualize_system_prompt: str,
        description: Optional[str],
        color: Optional[str],
        enum_model: str,
        max_response_tokens: int,
        temperature: float,
        history_message_count: int,
        knowledge_base_ids: Optional[List[UUID]],
        toolset_ids: Optional[List[UUID]],
    ):
        agent = Agent(
            name=name,
            description=description,
            color=color,
            prompt=prompt,
            contextualize_system_prompt=contextualize_system_prompt,
            enum_model=enum_model,
            max_response_tokens=max_response_tokens,
            temperature=temperature,
            history_message_count=history_message_count,
        )
        self.session.add(agent)
        await self.session.flush()
        await self.session.refresh(agent)
        self.agent = agent
        await self._sync_associations(knowledge_base_ids, toolset_ids)
        await self._refresh_related(agent)
        self.agent_schema = self._create_agent_schema(self.agent, self._knowledge_bases, self._toolsets)
        return self

    async def update(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        prompt: Optional[str] = None,
        contextualize_system_prompt: Optional[str] = None,
        enum_model: Optional[str] = None,
        max_response_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        history_message_count: Optional[int] = None,
        knowledge_base_ids: Optional[List[UUID]] = None,
        toolset_ids: Optional[List[UUID]] = None,
    ):
        if not self.agent:
            raise RuntimeError("Agent repository is not initialized.")

        if name is not None:
            self.agent.name = name
        if description is not None:
            self.agent.description = description
        if color is not None:
            self.agent.color = color
        if prompt is not None:
            self.agent.prompt = prompt
        if contextualize_system_prompt is not None:
            self.agent.contextualize_system_prompt = contextualize_system_prompt
        if enum_model is not None:
            self.agent.enum_model = enum_model
        if max_response_tokens is not None:
            self.agent.max_response_tokens = max_response_tokens
        if temperature is not None:
            self.agent.temperature = temperature
        if history_message_count is not None:
            self.agent.history_message_count = history_message_count

        await self.session.flush()
        await self.session.refresh(self.agent)

        await self._sync_associations(knowledge_base_ids, toolset_ids)
        await self._refresh_related(self.agent)
        self.agent_schema = self._create_agent_schema(self.agent, self._knowledge_bases, self._toolsets)
        return self

    async def delete(self):
        if not self.agent:
            raise RuntimeError("Agent repository is not initialized.")
        self.agent.is_active = False
        await self.session.flush()
        await self.session.refresh(self.agent)
        self.agent_schema = self._create_agent_schema(self.agent, self._knowledge_bases, self._toolsets)
        return self

    def get_agent(self) -> AgentSchema:
        return self.agent_schema

    @staticmethod
    async def paginate_agents(
        session: AsyncSession, page_number: int, page_size: int
    ) -> List[AgentSchema]:
        offset = (page_number - 1) * page_size
        stmt = (
            select(Agent)
            .where(Agent.is_active == True)
            .offset(offset)
            .limit(page_size)
            .order_by(Agent.created_at.desc())
        )
        result = await session.execute(stmt)
        agents = result.scalars().all()
        agent_ids = [agent.id for agent in agents]
        kb_map = await AgentRepository._fetch_knowledge_bases_map(session, agent_ids)
        toolset_map = await AgentRepository._fetch_toolsets_map(session, agent_ids)

        return [
            AgentRepository._create_agent_schema(
                agent,
                kb_map.get(agent.id, []),
                toolset_map.get(agent.id, []),
            )
            for agent in agents
        ]

    @staticmethod
    async def count_agents(session: AsyncSession) -> int:
        stmt = select(func.count(Agent.id)).where(Agent.is_active == True)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _sync_associations(
        self,
        knowledge_base_ids: Optional[List[UUID]],
        toolset_ids: Optional[List[UUID]],
    ):
        if not self.agent:
            raise RuntimeError("Agent repository is not initialized.")

        if knowledge_base_ids is not None:
            await self._validate_knowledge_base_ids(knowledge_base_ids)
            await self.session.execute(
                delete(AgentKnowledgeBaseAssociation).where(
                    AgentKnowledgeBaseAssociation.agent_id == self.agent.id
                )
            )
            if knowledge_base_ids:
                await self.session.execute(
                    insert(AgentKnowledgeBaseAssociation),
                    [
                        {"agent_id": self.agent.id, "knowledge_base_id": kb_id}
                        for kb_id in knowledge_base_ids
                    ],
                )

        if toolset_ids is not None:
            await self._validate_toolset_ids(toolset_ids)
            await self.session.execute(
                delete(AgentToolsetAssociation).where(
                    AgentToolsetAssociation.agent_id == self.agent.id
                )
            )
            if toolset_ids:
                await self.session.execute(
                    insert(AgentToolsetAssociation),
                    [
                        {"agent_id": self.agent.id, "toolset_id": toolset_id}
                        for toolset_id in toolset_ids
                    ],
                )

    async def _refresh_related(self, agent: Agent):
        kb_map = await self._fetch_knowledge_bases_map(self.session, [agent.id])
        toolset_map = await self._fetch_toolsets_map(self.session, [agent.id])
        self._knowledge_bases = kb_map.get(agent.id, [])
        self._toolsets = toolset_map.get(agent.id, [])

    async def _validate_knowledge_base_ids(self, knowledge_base_ids: List[UUID]):
        if not knowledge_base_ids:
            return
        stmt = select(KnowledgeBase.id).where(
            KnowledgeBase.id.in_(knowledge_base_ids),
            KnowledgeBase.is_active == True,
        )
        result = await self.session.execute(stmt)
        found_ids = {row[0] for row in result.all()}
        missing = set(knowledge_base_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge bases not found: {', '.join(str(mid) for mid in missing)}",
            )

    async def _validate_toolset_ids(self, toolset_ids: List[UUID]):
        if not toolset_ids:
            return
        stmt = select(Toolset.id).where(
            Toolset.id.in_(toolset_ids),
            Toolset.is_active == True,
        )
        result = await self.session.execute(stmt)
        found_ids = {row[0] for row in result.all()}
        missing = set(toolset_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Toolsets not found: {', '.join(str(mid) for mid in missing)}",
            )

    @staticmethod
    def _create_agent_schema(
        agent: Agent,
        knowledge_bases: List[KnowledgeBase],
        toolsets: List[Toolset],
    ) -> AgentSchema:
        return AgentSchema(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            color=agent.color,
            prompt=agent.prompt,
            contextualize_system_prompt=agent.contextualize_system_prompt,
            enum_model=agent.enum_model,
            max_response_tokens=agent.max_response_tokens,
            temperature=agent.temperature,
            history_message_count=agent.history_message_count,
            is_active=agent.is_active,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            knowledge_bases=[
                KnowledgeBaseRepository._create_knowledge_base_schema(kb, []) for kb in knowledge_bases
            ],
            toolsets=[
                ToolsetRepository.create_toolset_schema(toolset, []) for toolset in toolsets
            ],
        )

    @staticmethod
    async def _fetch_knowledge_bases_map(
        session: AsyncSession, agent_ids: List[UUID]
    ) -> Dict[UUID, List[KnowledgeBase]]:
        if not agent_ids:
            return {}
        stmt = (
            select(AgentKnowledgeBaseAssociation.agent_id, KnowledgeBase)
            .join(
                KnowledgeBase,
                KnowledgeBase.id == AgentKnowledgeBaseAssociation.knowledge_base_id,
            )
            .where(
                AgentKnowledgeBaseAssociation.agent_id.in_(agent_ids),
                KnowledgeBase.is_active == True,
            )
        )
        result = await session.execute(stmt)
        rows = result.all()
        kb_map: Dict[UUID, List[KnowledgeBase]] = {}
        for agent_id, knowledge_base in rows:
            kb_map.setdefault(agent_id, []).append(knowledge_base)
        return kb_map

    @staticmethod
    async def _fetch_toolsets_map(
        session: AsyncSession, agent_ids: List[UUID]
    ) -> Dict[UUID, List[Toolset]]:
        if not agent_ids:
            return {}
        stmt = (
            select(AgentToolsetAssociation.agent_id, Toolset)
            .join(Toolset, Toolset.id == AgentToolsetAssociation.toolset_id)
            .where(
                AgentToolsetAssociation.agent_id.in_(agent_ids),
                Toolset.is_active == True,
            )
        )
        result = await session.execute(stmt)
        rows = result.all()
        toolset_map: Dict[UUID, List[Toolset]] = {}
        for agent_id, toolset in rows:
            toolset_map.setdefault(agent_id, []).append(toolset)
        return toolset_map