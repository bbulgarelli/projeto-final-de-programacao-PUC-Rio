from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChunkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    page: int
    seq_num: int
    values: List[float]
    num_tokens: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    file_id: UUID
    file: Optional["FileSchema"] = None


class FileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    enum_status: str
    enum_type: Optional[str] = None
    num_pages: Optional[int] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    knowledge_base_id: Optional[UUID] = None
    knowledge_base: Optional["KnowledgeBaseSchema"] = None
    chunks: List[ChunkSchema] = Field(default_factory=list)


class KnowledgeBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    files: List[FileSchema] = Field(default_factory=list)

ChunkSchema.model_rebuild()
FileSchema.model_rebuild()


