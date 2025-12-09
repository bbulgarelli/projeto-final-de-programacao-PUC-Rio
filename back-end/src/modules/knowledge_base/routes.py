from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)

from src.database.session_manager import DBSessionDep
from .repositories.KnowledgeBaseRepository import (
    FileRepository,
    KnowledgeBaseRepository,
    create_file_repository,
    create_knowledge_base_repository,
    get_file_repository,
    get_knowledge_base_repository,
)
from .process_file.ProcessFile import ProcessFile, process_file_bg_task
from .routes_schemas import (
    FileListResponse,
    FileResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    UpdateFile,
    CreateKnowledgeBase,
    UpdateKnowledgeBase,
)

knowledge_base_router = APIRouter(tags=["Knowledge Base Management"])


@knowledge_base_router.post(
    "/knowledge-bases",
    status_code=status.HTTP_201_CREATED,
    response_model=KnowledgeBaseResponse,
)
async def create_knowledge_base(
    payload: CreateKnowledgeBase,
    session: DBSessionDep,
):
    """Create a new knowledge base with the provided name and description."""
    repo = await create_knowledge_base_repository(
        session=session,
        name=payload.name,
        description=payload.description,
    )
    await session.commit()
    return KnowledgeBaseResponse(**repo.get_knowledge_base().model_dump())


@knowledge_base_router.get(
    "/knowledge-bases",
    response_model=KnowledgeBaseListResponse,
)
async def list_knowledge_bases(
    session: DBSessionDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List knowledge bases using pagination parameters."""
    knowledge_bases = await KnowledgeBaseRepository.paginate_knowledge_bases(
        session, page_number, page_size
    )
    total = await KnowledgeBaseRepository.count_knowledge_bases(session)
    return KnowledgeBaseListResponse(
        total_knowledge_bases=total,
        knowledge_bases=[
            KnowledgeBaseResponse(**kb.model_dump()) for kb in knowledge_bases
        ],
    )


@knowledge_base_router.get(
    "/knowledge-bases/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def get_knowledge_base(knowledge_base_id: UUID, session: DBSessionDep):
    """Fetch a single knowledge base by its identifier."""
    repo = await get_knowledge_base_repository(session, knowledge_base_id)
    return KnowledgeBaseResponse(**repo.get_knowledge_base().model_dump())


@knowledge_base_router.patch(
    "/knowledge-bases/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: UpdateKnowledgeBase,
    session: DBSessionDep,
):
    """Update the name or description of an existing knowledge base."""
    repo = await get_knowledge_base_repository(session, knowledge_base_id)
    await repo.update(name=payload.name, description=payload.description)
    await session.commit()
    return KnowledgeBaseResponse(**repo.get_knowledge_base().model_dump())


@knowledge_base_router.delete(
    "/knowledge-bases/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_base(knowledge_base_id: UUID, session: DBSessionDep):
    """Remove a knowledge base and its associated files."""
    repo = await get_knowledge_base_repository(session, knowledge_base_id)
    await repo.delete()
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@knowledge_base_router.post(
    "/knowledge-bases/{knowledge_base_id}/files",
    status_code=status.HTTP_201_CREATED,
    response_model=FileResponse,
)
async def upload_file_to_knowledge_base(
    background_tasks: BackgroundTasks,
    knowledge_base_id: UUID,
    file: UploadFile = File(...),
    enum_type: Optional[str] = Form(None),
    session: DBSessionDep = None,
):
    """Upload a file to a knowledge base and trigger asynchronous processing."""
    kb_repo = await get_knowledge_base_repository(session, knowledge_base_id)

    # Create file record with 'processing' status
    repo = await create_file_repository(
        session=session,
        knowledge_base_id=knowledge_base_id,
        name=file.filename,
        enum_status="processing",
        enum_type=enum_type or (file.content_type or None)
    )
    
    background_tasks.add_task(process_file_bg_task, knowledge_base_id, repo.get_file().id, file)

    await session.commit()
    return FileResponse(**repo.get_file().model_dump())


@knowledge_base_router.get(
    "/knowledge-bases/{knowledge_base_id}/files",
    response_model=FileListResponse,
)
async def list_files_for_knowledge_base(
    knowledge_base_id: UUID,
    session: DBSessionDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List files belonging to a knowledge base using pagination parameters."""
    kb = await get_knowledge_base_repository(session, knowledge_base_id)
    files = await FileRepository.paginate_files_for_knowledge_base(
        session, knowledge_base_id, page_number, page_size
    )
    total = await FileRepository.count_files_for_knowledge_base(session, knowledge_base_id)
    return FileListResponse(
        total_files=total,
        files=[FileResponse(**file.model_dump()) for file in files],
    )


@knowledge_base_router.get(
    "/files/{file_id}",
    response_model=FileResponse,
)
async def get_file(file_id: UUID, session: DBSessionDep):
    """Fetch a single file stored in the knowledge base system."""
    repo = await get_file_repository(session, file_id)
    return FileResponse(**repo.get_file().model_dump())


@knowledge_base_router.patch(
    "/files/{file_id}",
    response_model=FileResponse,
)
async def update_file(file_id: UUID, payload: UpdateFile, session: DBSessionDep):
    """Update file metadata such as name, status, type, summary, or page count."""
    repo = await get_file_repository(session, file_id)
    await repo.update(
        name=payload.name,
        enum_status=payload.enum_status,
        enum_type=payload.enum_type,
        summary=payload.summary,
        num_pages=payload.num_pages,
    )
    await session.commit()
    return FileResponse(**repo.get_file().model_dump())


@knowledge_base_router.delete(
    "/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_file(file_id: UUID, session: DBSessionDep):
    """Delete a file from the knowledge base."""
    repo = await get_file_repository(session, file_id)
    await repo.delete()
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

