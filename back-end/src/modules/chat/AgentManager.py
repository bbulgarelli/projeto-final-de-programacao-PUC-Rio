from typing import AsyncGenerator, Callable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.toolsets.repositories.ToolsetRepository import get_toolset_repository
from src.modules.agents.repositories.AgentRepository import AgentRepository
from src.modules.chat.AgentExecutor import AgentExecutor, AgentExecutorResponse, AgentExecutorStreamResponse, BasicDependencies
from src.modules.chat.schemas import MessageSchema
from src.modules.chat.utils import get_pydantic_message_history
from src.modules.copilot.models import LLMModel
from src.modules.toolsets.ToolFactory import ToolsetFactory

async def get_agent_manager(session: AsyncSession, agent_repo: AgentRepository):
    agent_manager = AgentManager(agent_repo)
    await agent_manager.init(session)
    return agent_manager

class AgentManager:
    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    async def init(self, session: AsyncSession):
        self.toolsets = []
        if self.agent_repo.get_agent().toolsets:
            for toolset in self.agent_repo.get_agent().toolsets:
                toolset_repo = await get_toolset_repository(session, toolset.id)
                self.toolsets.append(await ToolsetFactory.get_pydantic_toolset(toolset_repo.get_toolset()))

    async def get_response(self, question: str, history: List[MessageSchema]) -> AgentExecutorResponse:
        agent_executor = AgentExecutor(
            prompt=self.agent_repo.get_agent().prompt,
            model=LLMModel(self.agent_repo.get_agent().enum_model),
            knowledge_bases=self.agent_repo.get_agent().knowledge_bases,
            toolsets=self.toolsets
        )
        return await agent_executor.get_response(BasicDependencies(message=question, chat_history=get_pydantic_message_history(history)))

    async def stream_response(
        self, question: str, history: List[MessageSchema], 
        callback: Optional[Callable[[AgentExecutorResponse], None]]
    ) -> AsyncGenerator[AgentExecutorStreamResponse, None]:
        agent_executor = AgentExecutor(
            prompt=self.agent_repo.get_agent().prompt,
            model=LLMModel(self.agent_repo.get_agent().enum_model),
            knowledge_bases=self.agent_repo.get_agent().knowledge_bases,
            toolsets=self.toolsets
        )
        async for event in agent_executor.stream_response(
            BasicDependencies(message=question, chat_history=get_pydantic_message_history(history)), 
            callback
        ):
            yield event