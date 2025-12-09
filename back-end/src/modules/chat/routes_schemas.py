from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateChat(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human readable title used to identify the conversation.",
    )


class UpdateChat(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="New title to replace the current conversation name.",
    )


class AskQuestionPayload(BaseModel):
    agent_id: UUID = Field(
        ...,
        description="Identifier of the agent that should answer the question.",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural language question that will be forwarded to the agent.",
    )


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., ge=1, description="Unique identifier of the stored message.")
    sent_at: datetime = Field(..., description="Timestamp when the user message was created.")
    message: str = Field(..., min_length=1, description="User message content.")
    response: Optional[str] = Field(
        default=None,
        description="Agent response content if already processed.",
    )
    input_tokens: int = Field(..., ge=0, description="Number of tokens received from the user.")
    reasoning_tokens: int = Field(..., ge=0, description="Number of tokens spent on reasoning steps.")
    output_tokens: int = Field(..., ge=0, description="Number of tokens returned to the user.")
    json_message_history: Optional[dict | list] = Field(
        default=None,
        description="Structured history used by the agent during reasoning.",
    )
    chat_id: UUID = Field(..., description="Identifier of the chat the message belongs to.")


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the chat.")
    title: str = Field(..., min_length=1, max_length=255, description="Chat display title.")
    created_at: datetime = Field(..., description="Timestamp when the chat was created.")
    updated_at: datetime = Field(..., description="Timestamp when the chat was last updated.")
    is_active: bool = Field(..., description="Flag indicating whether the chat is active.")
    messages: List[MessageResponse] = Field(
        default_factory=list,
        description="Ordered list of messages exchanged in the chat.",
    )


class ChatListResponse(BaseModel):
    total_chats: int = Field(..., ge=0, description="Total number of chats available.")
    chats: List[ChatResponse] = Field(
        default_factory=list,
        description="Paginated collection of chats.",
    )


class StreamMessageResponse(BaseModel):
    status: Literal[
        "searching",
        "tool_call",
        "tool_running",
        "tool_result",
        "response",
        "end_turn",
        "keepalive",
        "error",
    ] = Field(
        ...,
        description="Current streaming status emitted by the agent executor.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error details when status is 'error'.",
    )
    response: str = Field(
        default="",
        description="Partial or final response text emitted during streaming.",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Name of the tool being invoked when status reflects a tool action.",
    )
    tool_args: Optional[str] = Field(
        default=None,
        description="Serialized arguments passed to the tool call, if applicable.",
    )
    tool_result: Optional[str] = Field(
        default=None,
        description="Serialized tool result when available.",
    )
    info: Optional[str] = Field(
        default=None,
        description="Additional informational messages emitted during streaming.",
    )
