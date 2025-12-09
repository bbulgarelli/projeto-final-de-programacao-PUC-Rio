import uuid

from sqlalchemy import Integer, String, ForeignKey, Boolean,  DateTime, func, Index, Text, JSON, Float, SmallInteger, null
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB

from src.database.session_manager import Base
 

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'

    id = mapped_column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)
    name = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = mapped_column(Boolean, nullable=False, default=True)

    def __str__(self):
        return self.name

class File(Base):
    __tablename__ = 'file'

    id = mapped_column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)
    name = mapped_column(String(128), nullable=False)
    enum_status = mapped_column(String, nullable=False, default='active')
    enum_type = mapped_column(String, nullable=True)
    num_pages = mapped_column(Integer, nullable=True)
    summary = mapped_column(Text, nullable=True) 
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = mapped_column(Boolean, nullable=False, default=True)

    knowledge_base_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('knowledge_base.id'), nullable=True)

    def __str__(self):
        return self.name

class Chunk(Base):
    __tablename__ = 'chunk'

    id = mapped_column(UUID(as_uuid=True),
                       primary_key=True, default=uuid.uuid4)
    content = mapped_column(Text, nullable=False)
    page = mapped_column(Integer, nullable=False)
    seq_num = mapped_column(Integer, nullable=False)
    values = mapped_column(ARRAY(Float), nullable=False)
    num_tokens = mapped_column(Integer, nullable=True, default=0)
    created_at = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now())

    file_id = mapped_column(
        UUID(as_uuid=True), ForeignKey('file.id'), nullable=False)

    def __str__(self):
        return self.content
