from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from src.database.session_manager import DBSessionDep
from src.modules.agents.repositories.AgentRepository import (
    AgentRepository,
    create_agent_repository,
    get_agent_repository,
)
from .routes_schemas import (
    AgentListResponse,
    AgentResponse,
    CreateAgent,
    UpdateAgent,
)

agent_router = APIRouter(tags=["Agent Management"])


@agent_router.post(
    "/agents",
    status_code=status.HTTP_201_CREATED,
    response_model=AgentResponse,
)
async def create_agent(payload: CreateAgent, session: DBSessionDep):
    """Create a new agent with the provided configuration and linked resources."""
    repo = await create_agent_repository(
        session=session,
        name=payload.name,
        description=payload.description,
        color=payload.color,
        prompt=payload.prompt,
        contextualize_system_prompt=payload.contextualize_system_prompt,
        enum_model=payload.enum_model or "chatgpt_3_5_turbo",
        max_response_tokens=payload.max_response_tokens or 16000,
        temperature=payload.temperature or 1.0,
        history_message_count=payload.history_message_count or 10,
        knowledge_base_ids=payload.knowledge_base_ids,
        toolset_ids=payload.toolset_ids,
    )
    await session.commit()
    return AgentResponse(**repo.get_agent().model_dump())


@agent_router.get(
    "/agents",
    response_model=AgentListResponse,
)
async def list_agents(
    session: DBSessionDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List agents with pagination support."""
    agents = await AgentRepository.paginate_agents(session, page_number, page_size)
    total = await AgentRepository.count_agents(session)
    return AgentListResponse(
        total_agents=total,
        agents=[AgentResponse(**agent.model_dump()) for agent in agents],
    )


@agent_router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
)
async def get_agent(agent_id: UUID, session: DBSessionDep):
    """Retrieve an agent by its identifier."""
    repo = await get_agent_repository(session, agent_id)
    return AgentResponse(**repo.get_agent().model_dump())


@agent_router.patch(
    "/agents/{agent_id}",
    response_model=AgentResponse,
)
async def update_agent(agent_id: UUID, payload: UpdateAgent, session: DBSessionDep):
    """Update agent configuration and linked resources."""
    repo = await get_agent_repository(session, agent_id)
    await repo.update(
        name=payload.name,
        description=payload.description,
        color=payload.color,
        prompt=payload.prompt,
        contextualize_system_prompt=payload.contextualize_system_prompt,
        enum_model=payload.enum_model,
        max_response_tokens=payload.max_response_tokens,
        temperature=payload.temperature,
        history_message_count=payload.history_message_count,
        knowledge_base_ids=payload.knowledge_base_ids,
        toolset_ids=payload.toolset_ids,
    )
    await session.commit()
    return AgentResponse(**repo.get_agent().model_dump())


@agent_router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_agent(agent_id: UUID, session: DBSessionDep):
    """Delete an agent and remove its associations."""
    repo = await get_agent_repository(session, agent_id)
    await repo.delete()
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

