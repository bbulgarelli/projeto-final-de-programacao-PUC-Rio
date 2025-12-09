from typing import List, Dict, Any, Set
from uuid import UUID

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from sqlalchemy import select

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from openai import AsyncOpenAI

from src.config import settings
from src.database.session_manager import session_manager_provider
from src.modules.knowledge_base.models import File
from src.modules.knowledge_base.schemas import KnowledgeBaseSchema


class ContextManager:
    def __init__(self, knowledge_base: KnowledgeBaseSchema):
        self.knowledge_base = knowledge_base
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant_client = AsyncQdrantClient(url=settings.qdrant_url)

    async def get_context(self, message: str, chat_history: List[ModelMessage]) -> str:
        # 1. Use llm to trasform chat history and user's last question into a standalone question
        standalone_question = await self._create_standalone_question(message, chat_history)
        
        # 2. embed the standalone question
        embedding = await self._embed_question(standalone_question)
        
        # 3. search the knowledge base for the most relevant chunks
        chunks = await self._search_relevant_chunks(embedding)
        
        # 4. get the files ids from the chunks and get the files from the database
        files_map = await self._get_files_from_db(chunks)
        
        # 5. format the context into a string
        context = self._format_context(chunks, files_map)
        
        return context

    async def _create_standalone_question(self, message: str, chat_history: List[ModelMessage]) -> str:
        system_prompt = (
            "Given a chat history and the user's last question that may reference the context in the chat history, "
            "formulate a standalone question that can be understood without the chat history. "
            "DO NOT answer the question, just reformulate it if necessary and, otherwise, return it as it is."
        )
        agent = Agent(
            'openai:gpt-4o-mini',
            system_prompt=system_prompt
        )
        
        # Run agent to get standalone question
        # We pass the history as message_history, and the new message as user_prompt
        # Note: pydantic-ai might expect us to handle history carefully. 
        # If chat_history contains the last message, we should separate them or just pass history.
        # Assuming chat_history is previous history and 'message' is the new user prompt.
        
        result = await agent.run(message, message_history=chat_history)
        return result.output

    async def _embed_question(self, question: str) -> List[float]:
        response = await self.openai_client.embeddings.create(
            input=question,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    async def _search_relevant_chunks(self, embedding: List[float]) -> List[Any]:
        # Search in Qdrant
        collection_name = str(self.knowledge_base.id)
        
        # Check if collection exists to avoid errors (or assume it exists if KB is active)
        # We'll try to search, if it fails, return empty
        try:
            search_result = await self.qdrant_client.query_points(
                collection_name=collection_name,
                query=embedding,
                limit=30
            )
            return search_result.points
        except Exception:
            # Collection might not exist or other error
            return []

    async def _get_files_from_db(self, chunks: List[Any]) -> Dict[str, File]:
        file_ids: Set[str] = set()
        for point in chunks:
            if point.payload and "file_id" in point.payload:
                file_ids.add(point.payload["file_id"])
        
        if not file_ids:
            return {}

        async with session_manager_provider.get_session_manager().session() as session:
            stmt = select(File).where(File.id.in_([UUID(fid) for fid in file_ids]))
            result = await session.execute(stmt)
            files = result.scalars().all()
            
            return {str(f.id): f for f in files}

    def _format_context(self, chunks: List[Any], files_map: Dict[str, File]) -> str:
        # Group chunks by file_id to handle format structure which nests pages under file?
        # The prompt says:
        # <file name={file name} file_id={file id} >
        # <page number={page number} >
        # ...
        
        # And "the chunks must appear ordered by seq_num".
        # This implies we should process chunks in order of seq_num? 
        # But usually we want to group by file for the XML structure.
        # However, chunks from search are ordered by relevance (score).
        # If we reorder by seq_num, we lose relevance order, but gain reading coherence.
        # The instruction "chunks must appear ordered by seq_num" usually applies when we have multiple chunks from same doc.
        # But if we have chunks from different docs interspersed?
        # The XML format structure implies a hierarchy: File -> Page -> Content.
        # So we must group by File, then by Page (or just list pages).
        
        # Let's sort chunks by file_id then seq_num to satisfy the structure and ordering within file.
        # Or should we keep relevance order of files? 
        # Usually RAG prefers relevance. But strictly following the XML format:
        # <file ...> ... </file> implies grouping.
        
        # Strategy:
        # 1. Group chunks by file_id.
        # 2. Inside each file, sort by seq_num.
        # 3. Format.
        
        # Note: We might lose the "most relevant first" property across files, but we preserve it implicitly if we output files in order of their best chunk's score? 
        # Or just standard sort. The prompt is specific about format and seq_num.
        
        chunks_by_file: Dict[str, List[Any]] = {}
        for chunk in chunks:
            fid = chunk.payload.get("file_id")
            if fid:
                if fid not in chunks_by_file:
                    chunks_by_file[fid] = []
                chunks_by_file[fid].append(chunk)
        
        output_parts = []
        
        # We can iterate over files_map to ensure we have metadata, 
        # but we should probably iterate based on chunks to only include relevant files.
        # Let's iterate over the keys in chunks_by_file.
        
        for fid, file_chunks in chunks_by_file.items():
            file_obj = files_map.get(fid)
            if not file_obj:
                continue
                
            # Sort chunks by seq_num
            file_chunks.sort(key=lambda x: x.payload.get("seq_num", 0))
            
            file_header = f'<file name="{file_obj.name}" file_id="{fid}" >'
            output_parts.append(file_header)
            
            for chunk in file_chunks:
                page_num = chunk.payload.get("page", 0)
                content = chunk.payload.get("content", "")
                
                page_block = (
                    f'<page number="{page_num}" >\n'
                    f'<content>\n'
                    f'{content}\n'
                    f'</content>\n'
                    f'</page>'
                )
                output_parts.append(page_block)
                
            output_parts.append('</file>')
            
        return "\n".join(output_parts)
