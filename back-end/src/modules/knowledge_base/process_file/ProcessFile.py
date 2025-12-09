import os
import tempfile
import uuid
from typing import List, Dict, Any

from fastapi import UploadFile
from pydantic import BaseModel

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from pyzerox import zerox

from src.database.session_manager import session_manager_provider
from src.config import settings
from src.modules.knowledge_base.models import Chunk
from src.modules.knowledge_base.repositories.KnowledgeBaseRepository import FileRepository, KnowledgeBaseRepository, get_file_repository, get_knowledge_base_repository
from src.modules.knowledge_base.repositories.ChunkRepository import create_chunk_repository


class FileContent(BaseModel):
    class FilePage(BaseModel):
        page: int
        content: str
    pages: List[FilePage]

class ChunkedFileContent(BaseModel):
    class Chunks(BaseModel):
        content: str
        page: int
        seq_num: int
    chunks: List[Chunks]

class ProcessFile:

    def __init__(self, kb_repo: KnowledgeBaseRepository, file_repo: FileRepository):
        self.kb_repo = kb_repo
        self.file_repo = file_repo
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant_client = AsyncQdrantClient(url=settings.qdrant_url)

    async def get_file_content(self, file: UploadFile) -> FileContent:
        # Create temp file
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Ensure OPENAI_API_KEY is set for zerox
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            
            # Use py-zerox to get markdown
            # Using gpt-4o-mini as requested
            result = await zerox(file_path=tmp_path, model="gpt-4o-mini")
            
            pages = []
            # result.pages is expected to be a list of page objects with content
            for i, page in enumerate(result.pages):
                pages.append(FileContent.FilePage(page=i+1, content=page.content))
            
            return FileContent(pages=pages)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def chunk_file_content(self, file_content: FileContent) -> ChunkedFileContent:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
        )
        
        all_chunks = []
        seq_num_counter = 0
        
        for page in file_content.pages:
            chunks = text_splitter.split_text(page.content)
            for chunk_text in chunks:
                seq_num_counter += 1
                all_chunks.append(ChunkedFileContent.Chunks(
                    content=chunk_text,
                    page=page.page,
                    seq_num=seq_num_counter
                ))
                
        return ChunkedFileContent(chunks=all_chunks)

    async def embed_and_save_file_chunks(self, file_chunks: ChunkedFileContent) -> None:
        kb_id = str(self.kb_repo.knowledge_base.id)
        file_id = self.file_repo.file.id
        
        # Ensure collection exists
        # Check if collection exists first to avoid error or recreating
        collections = await self.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if kb_id not in collection_names:
            await self.qdrant_client.create_collection(
                collection_name=kb_id,
                vectors_config=qdrant_models.VectorParams(size=1536, distance=qdrant_models.Distance.COSINE),
            )

        points = []
        db_chunks = []
        
        for chunk in file_chunks.chunks:
            # Generate embedding
            response = await self.openai_client.embeddings.create(
                input=chunk.content,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Prepare Qdrant point
            chunk_id = uuid.uuid4()
            points.append(qdrant_models.PointStruct(
                id=str(chunk_id),
                vector=embedding,
                payload={
                    "content": chunk.content,
                    "page": chunk.page,
                    "seq_num": chunk.seq_num,
                    "file_id": str(file_id)
                }
            ))
            
            # Prepare DB Chunk
            db_chunks.append(Chunk(
                id=chunk_id,
                content=chunk.content,
                page=chunk.page,
                seq_num=chunk.seq_num,
                values=embedding,
                num_tokens=0, 
                file_id=file_id
            ))
            
        # Batch upsert to Qdrant
        if points:
            await self.qdrant_client.upsert(
                collection_name=kb_id,
                points=points
            )
            
        # Batch insert to Postgres
        if db_chunks:
            chunk_repo = await create_chunk_repository(self.file_repo.session)
            await chunk_repo.bulk_create(chunks=db_chunks)

    async def process_file(self, file: UploadFile) -> Dict[str, Any]:
        file_content = await self.get_file_content(file)
        chunked_file_content = await self.chunk_file_content(file_content)
        await self.embed_and_save_file_chunks(chunked_file_content)
        
        num_pages = len(file_content.pages)
        return {
            "summary": "File processed successfully.",
            "num_pages": num_pages
        }


async def process_file_bg_task(kb_id: uuid.UUID, file_id: uuid.UUID, file: UploadFile):
    async with session_manager_provider.get_session_manager().session() as session:
        kb_repo = await get_knowledge_base_repository(session, kb_id)
        file_repo = await get_file_repository(session, file_id)
        processor = ProcessFile(kb_repo, file_repo)
        try:
            # Process the file
            processor = ProcessFile(kb_repo, file_repo)
            processing_result = await processor.process_file(file)

            # Update file with processing results and set to 'active'
            await file_repo.update(
                enum_status="active",
                summary=processing_result.get("summary"),
                num_pages=processing_result.get("num_pages"),
            )
        except Exception as e:
            # Update status to failed if processing fails
            await file_repo.update(
                enum_status="failed",
                summary=f"Processing failed: {str(e)}"
            )
        await session.commit()