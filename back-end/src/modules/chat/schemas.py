from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sent_at: datetime
    message: str
    response: Optional[str] = None
    input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    json_message_history: Optional[dict | list] = None
    chat_id: UUID
    chat: Optional["ChatSchema"] = None


class ChatSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: List[MessageSchema] = Field(default_factory=list)


MessageSchema.model_rebuild()
ChatSchema.model_rebuild()

