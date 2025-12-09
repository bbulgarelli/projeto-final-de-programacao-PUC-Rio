import uuid
import enum

from sqlalchemy import Integer, String, ForeignKey, DateTime, func, Index, Enum, Text, Boolean, JSON, null
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.database.session_manager import Base

class Chat(Base):
    __tablename__ = 'chat'

    id = mapped_column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)
    title = mapped_column(String(255), nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = mapped_column(Boolean, nullable=False, default=True)


class Message(Base):
    __tablename__ = 'message'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    sent_at = mapped_column(DateTime, nullable=False, default=func.now())
    message = mapped_column(String, nullable=False)
    response = mapped_column(Text, nullable=True)
    input_tokens = mapped_column(Integer, nullable=False)
    reasoning_tokens = mapped_column(Integer, nullable=False)
    output_tokens = mapped_column(Integer, nullable=False)
    json_message_history = mapped_column(JSONB, nullable=True)

    chat_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('chat.id'), nullable=False)
 