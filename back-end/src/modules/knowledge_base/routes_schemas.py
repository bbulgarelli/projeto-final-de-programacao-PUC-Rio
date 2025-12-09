from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateKnowledgeBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human readable title that identifies the knowledge base.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional detailed explanation of the knowledge base purpose.",
    )


class UpdateKnowledgeBase(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New name for the knowledge base.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Updated description that clarifies the knowledge base content.",
    )


class FileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the uploaded file.")
    name: str = Field(..., min_length=1, max_length=255, description="Original name of the file.")
    enum_status: str = Field(
        ...,
        max_length=32,
        description="Processing status of the file (e.g., processing, ready, failed).",
    )
    enum_type: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Optional mime/type label or custom type for the file.",
    )
    num_pages: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of pages detected for the file, when available.",
    )
    summary: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional short summary generated from the file content.",
    )
    created_at: datetime = Field(..., description="Timestamp when the file entry was created.")
    updated_at: datetime = Field(..., description="Timestamp of the last file update.")
    is_active: bool = Field(..., description="Flag indicating if the file is active.")
    knowledge_base_id: Optional[UUID] = Field(
        default=None,
        description="Identifier of the knowledge base the file belongs to.",
    )
    chunks: List[dict] = Field(
        default_factory=list,
        description="Collection of processed content chunks linked to the file.",
    )


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(..., description="Unique identifier of the knowledge base.")
    name: str = Field(..., min_length=1, max_length=255, description="Name of the knowledge base.")
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the knowledge base.",
    )
    created_at: datetime = Field(..., description="Timestamp when the knowledge base was created.")
    updated_at: datetime = Field(..., description="Timestamp of the last knowledge base update.")
    is_active: bool = Field(..., description="Flag indicating if the knowledge base is active.")
    files: List[FileResponse] = Field(
        default_factory=list,
        description="Files stored inside the knowledge base.",
    )


class KnowledgeBaseListResponse(BaseModel):
    total_knowledge_bases: int = Field(
        ...,
        ge=0,
        description="Total number of knowledge bases that match the query.",
    )
    knowledge_bases: List[KnowledgeBaseResponse] = Field(
        default_factory=list,
        description="Paginated list of knowledge bases.",
    )


class UpdateFile(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New file name to display in listings.",
    )
    enum_status: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Updated processing status for the file.",
    )
    enum_type: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Updated file type label or mime type.",
    )
    num_pages: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated page count for the file.",
    )
    summary: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="New summary describing the file content.",
    )


class FileListResponse(BaseModel):
    total_files: int = Field(..., ge=0, description="Total number of files in the result set.")
    files: List[FileResponse] = Field(
        default_factory=list,
        description="Paginated collection of files.",
    )