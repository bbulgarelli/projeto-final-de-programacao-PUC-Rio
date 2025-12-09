from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.knowledge_base.models import Chunk
from src.modules.knowledge_base.schemas import ChunkSchema


async def create_chunk_repository(session: AsyncSession) -> "ChunkRepository":
    """Factory to create a chunk repository following existing patterns."""
    return ChunkRepository(session)


class ChunkRepository:
    """
    Repository for managing Chunk entities.

    Primarily handles bulk creation and retrieval of chunks associated with files.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self._chunks: List[Chunk] = []
        self._chunk_schemas: List[ChunkSchema] = []

    async def bulk_create(self, *, chunks: List[Chunk]) -> "ChunkRepository":
        """Persist a list of Chunk models in one batch."""
        if not chunks:
            return self

        self.session.add_all(chunks)
        await self.session.flush()
        # Refreshing only if needed later; here we keep objects as-is for performance.
        self._chunks = chunks
        self._chunk_schemas = [self.chunk_model_to_schema(chunk) for chunk in chunks]
        return self

    def get_chunks(self) -> List[ChunkSchema]:
        return self._chunk_schemas

    @staticmethod
    def chunk_model_to_schema(chunk: Chunk) -> ChunkSchema:
        return ChunkSchema(
            id=chunk.id,
            content=chunk.content,
            page=chunk.page,
            seq_num=chunk.seq_num,
            values=chunk.values,
            num_tokens=chunk.num_tokens,
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
            file_id=chunk.file_id,
            file=None,
        )

