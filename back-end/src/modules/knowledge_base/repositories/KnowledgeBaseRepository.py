from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.knowledge_base.models import File, KnowledgeBase
from src.modules.knowledge_base.schemas import FileSchema, KnowledgeBaseSchema


async def get_knowledge_base_repository(
    session: AsyncSession, knowledge_base_id: UUID
) -> "KnowledgeBaseRepository":
    """
    Factory to create a KnowledgeBaseRepository instance and load an existing knowledge base.

    Args:
        session (AsyncSession): The database session.
        knowledge_base_id (UUID): The unique identifier of the knowledge base.

    Returns:
        KnowledgeBaseRepository: An instance of the repository with the loaded knowledge base.
    """
    repo = KnowledgeBaseRepository(session)
    await repo.load(knowledge_base_id)
    return repo


async def create_knowledge_base_repository(
    session: AsyncSession,
    *,
    name: str,
    description: Optional[str],
) -> "KnowledgeBaseRepository":
    """
    Factory to create a KnowledgeBaseRepository instance and a new knowledge base.

    Args:
        session (AsyncSession): The database session.
        name (str): The name of the knowledge base.
        description (Optional[str]): A description of the knowledge base.

    Returns:
        KnowledgeBaseRepository: An instance of the repository with the created knowledge base.
    """
    repo = KnowledgeBaseRepository(session)
    await repo.create(name=name, description=description)
    return repo


async def get_file_repository(session: AsyncSession, file_id: UUID) -> "FileRepository":
    """
    Factory to create a FileRepository instance and load an existing file.

    Args:
        session (AsyncSession): The database session.
        file_id (UUID): The unique identifier of the file.

    Returns:
        FileRepository: An instance of the repository with the loaded file.
    """
    repo = FileRepository(session)
    await repo.load(file_id)
    return repo


async def create_file_repository(
    session: AsyncSession,
    *,
    knowledge_base_id: Optional[UUID],
    name: str,
    enum_status: Optional[str],
    enum_type: Optional[str],
    summary: Optional[str] = None,
    num_pages: Optional[int] = None,
) -> "FileRepository":
    """
    Factory to create a FileRepository instance and a new file record.

    Args:
        session (AsyncSession): The database session.
        knowledge_base_id (Optional[UUID]): ID of the knowledge base the file belongs to.
        name (str): The name of the file.
        enum_status (Optional[str]): The processing status of the file.
        enum_type (Optional[str]): The type of the file.
        summary (Optional[str], optional): A summary of the file content.
        num_pages (Optional[int], optional): Number of pages in the file.

    Returns:
        FileRepository: An instance of the repository with the created file.
    """
    repo = FileRepository(session)
    await repo.create(
        knowledge_base_id=knowledge_base_id,
        name=name,
        enum_status=enum_status,
        enum_type=enum_type,
        summary=summary,
        num_pages=num_pages,
    )
    return repo


class KnowledgeBaseRepository:
    """
    Repository for managing KnowledgeBase entities.

    Handles lifecycle operations for knowledge bases and their associated files.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.knowledge_base: Optional[KnowledgeBase] = None
        self._files: List[File] = []

    async def load(self, knowledge_base_id: UUID):
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.is_active == True,
        )
        result = await self.session.execute(stmt)
        knowledge_base = result.scalar_one_or_none()
        if not knowledge_base:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
        self.knowledge_base = knowledge_base
        await self._refresh_files()
        self.knowledge_base_schema = self._create_knowledge_base_schema(self.knowledge_base, self._files)
        return self

    async def create(self, *, name: str, description: Optional[str]):
        self.knowledge_base = KnowledgeBase(name=name, description=description)
        self.session.add(self.knowledge_base)
        await self.session.flush()
        await self.session.refresh(self.knowledge_base)
        self.knowledge_base_schema = self._create_knowledge_base_schema(self.knowledge_base, [])
        self._files = []
        return self

    async def update(self, *, name: Optional[str], description: Optional[str]):
        if not self.knowledge_base:
            raise RuntimeError("Knowledge base repository is not initialized.")

        if name is not None:
            self.knowledge_base.name = name
        if description is not None:
            self.knowledge_base.description = description

        await self.session.flush()
        await self.session.refresh(self.knowledge_base)
        self.knowledge_base_schema = self._create_knowledge_base_schema(self.knowledge_base, self._files)
        return self

    async def delete(self):
        if not self.knowledge_base:
            raise RuntimeError("Knowledge base repository is not initialized.")
        self.knowledge_base.is_active = False
        await self.session.flush()
        await self.session.refresh(self.knowledge_base)
        self.knowledge_base_schema = self._create_knowledge_base_schema(self.knowledge_base, self._files)
        return self

    def get_knowledge_base(self) -> KnowledgeBaseSchema:
        return self.knowledge_base_schema

    @staticmethod
    async def paginate_knowledge_bases(
        session: AsyncSession, page_number: int, page_size: int
    ) -> List[KnowledgeBaseSchema]:
        offset = (page_number - 1) * page_size
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.is_active == True)
            .offset(offset)
            .limit(page_size)
            .order_by(KnowledgeBase.created_at.desc())
        )
        result = await session.execute(stmt)
        knowledge_bases = result.scalars().all()
        kb_ids = [kb.id for kb in knowledge_bases]
        file_map = await KnowledgeBaseRepository._fetch_files_map(session, kb_ids)
        return [
            KnowledgeBaseRepository._create_knowledge_base_schema(
                kb, file_map.get(kb.id, [])
            )
            for kb in knowledge_bases
        ]

    @staticmethod
    async def count_knowledge_bases(session: AsyncSession) -> int:
        stmt = select(func.count(KnowledgeBase.id)).where(KnowledgeBase.is_active == True)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _refresh_files(self):
        if not self.knowledge_base:
            return
        file_map = await self._fetch_files_map(self.session, [self.knowledge_base.id])
        self._files = file_map.get(self.knowledge_base.id, [])

    @staticmethod
    def _create_knowledge_base_schema(
        knowledge_base: KnowledgeBase,
        files: List[File],
    ) -> KnowledgeBaseSchema:
        kb_dict = {
            "id": knowledge_base.id,
            "name": knowledge_base.name,
            "description": knowledge_base.description,
            "created_at": knowledge_base.created_at,
            "updated_at": knowledge_base.updated_at,
            "is_active": knowledge_base.is_active,
            "files": [
                FileSchema(
                    id=file.id,
                    name=file.name,
                    enum_status=file.enum_status,
                    enum_type=file.enum_type,
                    num_pages=file.num_pages,
                    summary=file.summary,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                    is_active=file.is_active,
                    knowledge_base_id=file.knowledge_base_id,
                    knowledge_base=None,
                    chunks=[],
                )
                for file in files
                if file.is_active
            ],
        }
        return KnowledgeBaseSchema(**kb_dict)

    @staticmethod
    async def _fetch_files_map(
        session: AsyncSession, knowledge_base_ids: List[UUID]
    ) -> Dict[UUID, List[File]]:
        if not knowledge_base_ids:
            return {}
        stmt = (
            select(File)
            .where(
                File.knowledge_base_id.in_(knowledge_base_ids),
                File.is_active == True,
            )
        )
        result = await session.execute(stmt)
        files = result.scalars().all()
        file_map: Dict[UUID, List[File]] = {}
        for file in files:
            file_map.setdefault(file.knowledge_base_id, []).append(file)
        return file_map


class FileRepository:
    """
    Repository for managing File entities within knowledge bases.

    Handles CRUD operations for files.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.file: Optional[File] = None

    async def load(self, file_id: UUID):
        stmt = select(File).where(File.id == file_id, File.is_active == True)
        result = await self.session.execute(stmt)
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        self.file = file
        self.file_schema = self.file_model_to_schema(self.file)
        return self

    async def create(
        self,
        *,
        knowledge_base_id: Optional[UUID],
        name: str,
        enum_status: Optional[str],
        enum_type: Optional[str],
        summary: Optional[str],
        num_pages: Optional[int],
    ):
        file = File(
            knowledge_base_id=knowledge_base_id,
            name=name,
            enum_status=enum_status or "active",
            enum_type=enum_type,
            summary=summary,
            num_pages=num_pages,
        )
        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)
        self.file = file
        self.file_schema = self.file_model_to_schema(self.file)
        return self

    async def update(
        self,
        *,
        name: Optional[str] = None,
        enum_status: Optional[str] = None,
        enum_type: Optional[str] = None,
        summary: Optional[str] = None,
        num_pages: Optional[int] = None,
    ):
        if not self.file:
            raise RuntimeError("File repository is not initialized.")

        if name is not None:
            self.file.name = name
        if enum_status is not None:
            self.file.enum_status = enum_status
        if enum_type is not None:
            self.file.enum_type = enum_type
        if summary is not None:
            self.file.summary = summary
        if num_pages is not None:
            self.file.num_pages = num_pages

        await self.session.flush()
        await self.session.refresh(self.file)
        self.file_schema = self.file_model_to_schema(self.file)
        return self

    async def delete(self):
        if not self.file:
            raise RuntimeError("File repository is not initialized.")
        self.file.is_active = False
        await self.session.flush()
        await self.session.refresh(self.file)
        self.file_schema = self.file_model_to_schema(self.file)
        return self

    def get_file(self) -> FileSchema:
        return self.file_schema

    @staticmethod
    async def paginate_files_for_knowledge_base(
        session: AsyncSession, knowledge_base_id: UUID, page_number: int, page_size: int
    ) -> List[FileSchema]:
        offset = (page_number - 1) * page_size
        stmt = (
            select(File)
            .where(
                File.knowledge_base_id == knowledge_base_id,
                File.is_active == True,
            )
            .offset(offset)
            .limit(page_size)
            .order_by(File.created_at.desc())
        )
        result = await session.execute(stmt)
        files = result.scalars().all()
        return [
            FileSchema(
                id=file.id,
                name=file.name,
                enum_status=file.enum_status,
                enum_type=file.enum_type,
                num_pages=file.num_pages,
                summary=file.summary,
                created_at=file.created_at,
                updated_at=file.updated_at,
                is_active=file.is_active,
                knowledge_base_id=file.knowledge_base_id,
                knowledge_base=None,
                chunks=[],
            )
            for file in files
        ]

    @staticmethod
    async def count_files_for_knowledge_base(
        session: AsyncSession, knowledge_base_id: UUID
    ) -> int:
        stmt = select(func.count(File.id)).where(
            File.knowledge_base_id == knowledge_base_id,
            File.is_active == True,
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def file_model_to_schema(file: File) -> FileSchema:
        return FileSchema(
            id=file.id,
            name=file.name,
            enum_status=file.enum_status,
            enum_type=file.enum_type,
            num_pages=file.num_pages,
            summary=file.summary,
            created_at=file.created_at,
            updated_at=file.updated_at,
            is_active=file.is_active,
        )