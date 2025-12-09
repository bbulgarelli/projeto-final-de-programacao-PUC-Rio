from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from pydantic_ai import ModelMessage
from pydantic_core import to_jsonable_python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.chat.models import Chat, Message
from src.modules.chat.schemas import ChatSchema, MessageSchema


async def get_chat_repository(session: AsyncSession, chat_id: UUID) -> "ChatRepository":
    """
    Factory to create a ChatRepository instance and load an existing chat.

    Args:
        session (AsyncSession): The database session.
        chat_id (UUID): The unique identifier of the chat to load.

    Returns:
        ChatRepository: An instance of the repository with the loaded chat.
    """
    repo = ChatRepository(session)
    await repo.load(chat_id)
    return repo


async def create_chat_repository(session: AsyncSession, *, title: str) -> "ChatRepository":
    """
    Factory to create a ChatRepository instance and a new chat.

    Args:
        session (AsyncSession): The database session.
        title (str): The title of the new chat.

    Returns:
        ChatRepository: An instance of the repository with the created chat.
    """
    repo = ChatRepository(session)
    await repo.create(title=title)
    return repo


class ChatRepository:
    """
    Repository for managing Chat entities and their messages.

    Handles creation, retrieval, updates, and deletion of chats,
    as well as adding messages to a chat.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat: Optional[Chat] = None
        self._messages: List[Message] = []

    async def load(self, chat_id: UUID):
        stmt = select(Chat).where(Chat.id == chat_id, Chat.is_active == True)
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        self.chat = chat
        await self._refresh_messages()
        self.chat_schema = self._create_chat_schema(self.chat, self._messages)
        return self

    async def create(self, *, title: str):
        chat = Chat(title=title)
        self.session.add(chat)
        await self.session.flush()
        await self.session.refresh(chat)
        self.chat = chat
        self._messages = []
        self.chat_schema = self._create_chat_schema(self.chat, self._messages)
        return self

    async def update_title(self, *, title: str):
        if not self.chat:
            raise RuntimeError("Chat repository is not initialized.")
        self.chat.title = title
        await self.session.flush()
        await self.session.refresh(self.chat)
        self.chat_schema = self._create_chat_schema(self.chat, self._messages)
        return self

    async def delete(self):
        if not self.chat:
            raise RuntimeError("Chat repository is not initialized.")
        self.chat.is_active = False
        await self.session.flush()
        await self.session.refresh(self.chat)
        self.chat_schema = self._create_chat_schema(self.chat, self._messages)
        return self

    async def add_message(
        self,
        *,
        message: str,
        response: str,
        input_tokens: int,
        reasoning_tokens: int,
        output_tokens: int,
        json_message_history: Optional[List[ModelMessage]] = None,
    ) -> MessageSchema:
        if not self.chat:
            raise RuntimeError("Chat repository is not initialized.")

        message_model = Message(
            chat_id=self.chat.id,
            message=message,
            response=response,
            input_tokens=input_tokens,
            reasoning_tokens=reasoning_tokens,
            output_tokens=output_tokens,
            json_message_history=ChatRepository.format_message_history(json_message_history),
        )

        self.session.add(message_model)
        await self.session.flush()
        await self.session.refresh(message_model)
        self._messages.append(message_model)
        self.chat_schema = self._create_chat_schema(self.chat, self._messages)
        return ChatRepository.create_message_schema(message_model)

    def get_chat(self) -> ChatSchema:
        return self.chat_schema

    def list_messages(self) -> List[MessageSchema]:
        return [MessageSchema.model_validate(message) for message in self._messages]

    @staticmethod
    def format_message_history(message_history: List[ModelMessage]) -> List[Dict]:
        formatted_message_history = to_jsonable_python(message_history)
        for msg in formatted_message_history:
            msg.pop("usage", None)
            msg.pop("instructions", None)
        return formatted_message_history

    @staticmethod
    async def paginate_chats(
        session: AsyncSession, page_number: int, page_size: int
    ) -> List[ChatSchema]:
        offset = (page_number - 1) * page_size
        stmt = (
            select(Chat)
            .where(Chat.is_active == True)
            .offset(offset)
            .limit(page_size)
            .order_by(Chat.created_at.desc())
        )
        result = await session.execute(stmt)
        chats = result.scalars().all()
        return [
            ChatRepository._create_chat_schema(chat, [])
            for chat in chats
        ]

    @staticmethod
    async def count_chats(session: AsyncSession) -> int:
        stmt = select(func.count(Chat.id)).where(Chat.is_active == True)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _refresh_messages(self):
        if not self.chat:
            return
        stmt = (
            select(Message)
            .where(Message.chat_id == self.chat.id)
            .order_by(Message.sent_at.asc())
        )
        result = await self.session.execute(stmt)
        self._messages = result.scalars().all()

    @staticmethod
    def _create_chat_schema(chat: Chat, messages: List[Message]) -> ChatSchema:
        return ChatSchema(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            is_active=chat.is_active,
            messages=[ChatRepository.create_message_schema(msg) for msg in messages],
        )

    @staticmethod
    def create_message_schema(message: Message) -> MessageSchema:
        return MessageSchema(
            id=message.id,
            sent_at=message.sent_at,
            message=message.message,
            response=message.response,
            input_tokens=message.input_tokens,
            reasoning_tokens=message.reasoning_tokens,
            output_tokens=message.output_tokens,
            json_message_history=message.json_message_history,
            chat_id=message.chat_id,
        )