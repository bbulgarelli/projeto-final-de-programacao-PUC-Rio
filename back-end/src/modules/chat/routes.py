from typing import AsyncGenerator, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query, Response, status
from sse_starlette import EventSourceResponse

from src.modules.chat.AgentExecutor import AgentExecutorResponse, AgentExecutorStreamResponse
from src.modules.agents.repositories.AgentRepository import get_agent_repository
from src.modules.chat.AgentManager import get_agent_manager
from src.database.session_manager import DBSessionDep, session_manager_provider
from .repositories.ChatRepository import (
    ChatRepository,
    create_chat_repository,
    get_chat_repository,
)
from .routes_schemas import (
    AskQuestionPayload,
    ChatListResponse,
    ChatResponse,
    CreateChat,
    MessageResponse,
    StreamMessageResponse,
    UpdateChat,
)
from .schemas import MessageSchema

chat_router = APIRouter(tags=["Chat Management"])


async def mock_invoke_agent(agent_id: UUID, question: str, history: List[MessageSchema]) -> dict:
    """Mock function to simulate an agent response."""
    response_text = f"Agent {agent_id} says: I received your question '{question}'."
    input_tokens = max(1, len(question.split()))
    output_tokens = max(1, len(response_text.split()))
    reasoning_tokens = max(1, (input_tokens + output_tokens) // 2)
    return {
        "response": response_text,
        "input_tokens": input_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_tokens": output_tokens,
        "json_message_history": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response_text},
        ],
    }   


@chat_router.post(
    "/chats",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatResponse,
)
async def create_chat(payload: CreateChat, session: DBSessionDep):
    """Create a new chat conversation with the provided title."""
    repo = await create_chat_repository(session=session, title=payload.title)
    await session.commit()
    return ChatResponse(**repo.get_chat().model_dump())


@chat_router.get(
    "/chats",
    response_model=ChatListResponse,
)
async def list_chats(
    session: DBSessionDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all chats using pagination metadata."""
    chats = await ChatRepository.paginate_chats(session, page_number, page_size)
    total = await ChatRepository.count_chats(session)
    return ChatListResponse(
        total_chats=total,
        chats=[ChatResponse(**chat.model_dump()) for chat in chats],
    )


@chat_router.get(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def get_chat(chat_id: UUID, session: DBSessionDep):
    """Retrieve a single chat by its identifier."""
    repo = await get_chat_repository(session, chat_id)
    return ChatResponse(**repo.get_chat().model_dump())


@chat_router.patch(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def update_chat(chat_id: UUID, payload: UpdateChat, session: DBSessionDep):
    """Update the title of an existing chat."""
    repo = await get_chat_repository(session, chat_id)
    await repo.update_title(title=payload.title)
    await session.commit()
    return ChatResponse(**repo.get_chat().model_dump())


@chat_router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat(chat_id: UUID, session: DBSessionDep):
    """Delete a chat and all related messages."""
    repo = await get_chat_repository(session, chat_id)
    await repo.delete()
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@chat_router.post(
    "/chats/{chat_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
)
async def ask_question(chat_id: UUID, payload: AskQuestionPayload, session: DBSessionDep):
    """Submit a question to an agent within a chat and store the resulting message."""
    chat_repo = await get_chat_repository(session, chat_id)
    agent_repo = await get_agent_repository(session, payload.agent_id)
    history = chat_repo.list_messages()
    agent_manager = await get_agent_manager(session, agent_repo)
    agent_response = await agent_manager.get_response(payload.question, history)
    message = await chat_repo.add_message(
        message=payload.question,
        response=agent_response.response,
        input_tokens=0,
        reasoning_tokens=0,
        output_tokens=0,
        json_message_history=agent_response.message_history,
    )
    await session.commit()
    return message


@chat_router.post(
    "/chats/{chat_id}/messages/stream",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def stream_question(
    chat_id: UUID,
    payload: AskQuestionPayload,
    session: DBSessionDep,
    background_tasks: BackgroundTasks
):
    """Stream an agent response for a question while persisting the final message."""
    async def callback(agent_response: AgentExecutorResponse):
        async with session_manager_provider.get_session_manager().session() as session:
            chat_repo = await get_chat_repository(session, chat_id)
            await chat_repo.add_message(
                message=payload.question,
                response=agent_response.response,
                input_tokens=0,
                reasoning_tokens=0,
                output_tokens=0,
                json_message_history=agent_response.message_history,
            )
            await session.commit()

    def background_callback(agent_response: AgentExecutorResponse):
        background_tasks.add_task(callback, agent_response)

    async def stream_response(agent_manager_stream: AsyncGenerator[AgentExecutorStreamResponse, None]):
        async for event in agent_manager_stream:
            yield {
                "event": "message",
                "data": StreamMessageResponse(**event.model_dump())
            }
        yield {
            "event": "end",
            "data": None
        }

    chat_repo = await get_chat_repository(session, chat_id)
    agent_repo = await get_agent_repository(session, payload.agent_id)
    history = chat_repo.list_messages()
    agent_manager = await get_agent_manager(session, agent_repo)
    
    return EventSourceResponse(
        stream_response(
            agent_manager.stream_response(
                payload.question, 
                history,
                background_callback
            )
        )
    )