import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Dict, List, Literal, Optional, Tuple
from uuid import UUID
import httpx
from pydantic_ai import AudioUrl, DocumentUrl, ImageUrl, RunContext, Agent as PydanticAgent
from pydantic_ai.messages import (
    FunctionToolCallEvent, FunctionToolResultEvent, ModelMessage, ModelMessagesTypeAdapter,
    PartDeltaEvent, PartStartEvent, TextPart, TextPartDelta, ThinkingPartDelta
)
from pydantic_ai.toolsets import FunctionToolset
from pydantic_ai.messages import ModelRequest, UserPromptPart

from pydantic import BaseModel
from src.modules.knowledge_base.ContextManager import ContextManager
from src.modules.chat.utils import chunked_gather
from src.modules.knowledge_base.schemas import KnowledgeBaseSchema
from src.modules.agents.schemas import AgentSchema
from src.modules.copilot.models import LLMModel

# ========= Tool Call Dependencies =========


class ToolsetDependencies(BaseModel):
    id: str
    metadata: Any


@dataclass
class BasicDependencies:
    chat_history: Optional[List[ModelMessage]] = None
    message: Optional[str] = None
    total_tokens: int = 0
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
# ===========================================

# ========= Agent Executor Responses =========


class AgentExecutorResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    success: bool = True
    error: Optional[str] = None
    message_history: Optional[List[ModelMessage]] = None
    response: str



class AgentExecutorStreamResponse(BaseModel):
    status: Literal[
        "searching", "thinking", "tool_call",
        "tool_running", "tool_result", "response", "end_turn", "keepalive", "error",
    ]
    error: Optional[str] = None
    response: str = ""
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    tool_result: Optional[str] = None
    info: Optional[str] = None


class AgentExecutor:
    def __init__(
        self,
        prompt: str,
        model: LLMModel = LLMModel.gemini_2_0_flash,
        knowledge_bases: List[KnowledgeBaseSchema] = [],
        toolsets: Optional[List[FunctionToolset]] = None,
        # TODO: verify if model supports documents
    ):
        self.model = model
        self.prompt = prompt
        self.knowledge_bases = knowledge_bases
        self.toolsets = toolsets
        self.final_prompt: Optional[str] = None

        self.agent = PydanticAgent(
            model.get_pydantic_ai_model(),
            deps_type=BasicDependencies,
            toolsets=self.toolsets if self.toolsets else None
        )

    async def _get_context(self, dependencies: BasicDependencies, chat_history: List[ModelMessage] = [], message: Optional[str] = None) -> str:
        async def run_get_context(knowledge_base: KnowledgeBaseSchema) -> str:
            try:
                return await ContextManager(knowledge_base).get_context(message, chat_history)
            except Exception as e:
                raise e

        context = ["<contexto>"]
        tasks = [run_get_context(knowledge_base)
                 for knowledge_base in self.knowledge_bases]
        data_sources_responses: List[str]
        data_sources_responses, errors = await chunked_gather(tasks)
        for error, data_source_response in zip(errors, data_sources_responses):
            if isinstance(error, Exception):
                raise error
            context.append(data_source_response)
        context.append("</contexto>")
        context = "".join(context) if len(context) > 2 else ""
        print(context, flush=True)
        return context

    async def get_response(
        self, dependencies: BasicDependencies
    ) -> AgentExecutorResponse:
        @self.agent.instructions
        async def create_instructions(ctx: RunContext[BasicDependencies]) -> str:
            context = await self._get_context(ctx.deps, ctx.deps.chat_history, ctx.deps.message)
            return f"{self.prompt}\n\n{context}"

        try:
            result = await self.agent.run(
                dependencies.message,
                deps=dependencies,
                message_history=dependencies.chat_history or None
            )
        except httpx.HTTPStatusError as e:
            return AgentExecutorResponse(
                success=False,
                error=str(e),
                response=f"Ocorreu um erro ao executar o agente, provavelmente um link utilizado é inválido: {str(e)}\n{trace_msg}"
            )
        except Exception as e:
            trace_msg = ""
            return AgentExecutorResponse(
                success=False,
                error=str(e),
                response=f"Ocorreu um erro ao executar o agente.\n{trace_msg}"
            )

        message_history = result.new_messages()
        usage = result.usage()

        return AgentExecutorResponse(
            response=result.output,
            message_history=message_history,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens
        )

    def _emit_callback_final(
        self, callback: Optional[Callable], output: str, message_history: List[ModelMessage], input_tokens: int, output_tokens: int
    ):
        if not callback:
            return
        callback(AgentExecutorResponse(
            response=output,
            message_history=message_history,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        ))

    async def _pump_stream(self, dependencies: BasicDependencies, callback: Optional[Callable[[AgentExecutorResponse], None]] = None):
        all_messages = None
        try:
            @self.agent.instructions
            async def create_instructions(ctx: RunContext[BasicDependencies]) -> str:
                await ctx.deps.queue.put(AgentExecutorStreamResponse(
                    status="searching",
                    info="Buscando informações..."
                ))
                context = await self._get_context(ctx.deps, ctx.deps.chat_history, ctx.deps.message)
                return f"{self.prompt}\n\n{context}"

            error_occurred = False
            async with self.agent.iter(
                dependencies.message,
                deps=dependencies,
                message_history=dependencies.chat_history or None
            ) as run:
                async for node in run:
                    if PydanticAgent.is_model_request_node(node):
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartDeltaEvent):
                                    if isinstance(event.delta, ThinkingPartDelta):
                                        await dependencies.queue.put(AgentExecutorStreamResponse(
                                            status="thinking",
                                            info=event.delta.content_delta
                                        ))
                                    elif isinstance(event.delta, TextPartDelta):
                                        await dependencies.queue.put(AgentExecutorStreamResponse(
                                            status="response",
                                            response=event.delta.content_delta
                                        ))
                                    # elif isinstance(event.delta, ToolCallPartDelta):
                                    #     yield AgentExecutorStreamResponse(
                                    #         status="tool_call_delta",
                                    #         response=f"Tool call delta: {event.delta}",
                                    #         tool_delta=str(event.delta)
                                    #     )
                                elif isinstance(event, PartStartEvent):
                                    if isinstance(event.part, TextPart):
                                        await dependencies.queue.put(AgentExecutorStreamResponse(
                                            status="response",
                                            response=event.part.content
                                        ))

                    elif PydanticAgent.is_call_tools_node(node):
                        async with node.stream(run.ctx) as tool_stream:
                            async for event in tool_stream:
                                if isinstance(event, FunctionToolCallEvent):
                                    await dependencies.queue.put(AgentExecutorStreamResponse(
                                        status="tool_call",
                                        info=f"Chamando ferramenta.",
                                        tool_name=event.part.tool_name,
                                        tool_args=str(event.part.args)
                                    ))

                                elif isinstance(event, FunctionToolResultEvent):
                                    await dependencies.queue.put(AgentExecutorStreamResponse(
                                        status="tool_result",
                                        info=f"Ferramenta concluída.",
                                        tool_name=event.result.tool_name,
                                        tool_result=str(event.result.content)
                                    ))
                output = run.result.output
                message_history = run.result.new_messages()
                usage = run.result.usage()
                self._emit_callback_final(
                    callback, output, message_history, usage.input_tokens, usage.output_tokens)
        except httpx.HTTPStatusError as e:
            await dependencies.queue.put(AgentExecutorStreamResponse(
                status="error",
                error=str(e),
                response=f"Ocorreu um erro ao executar o agente, provavelmente um link utilizado é inválido: {str(e)}\n"
            ))
        except Exception as e:
            await dependencies.queue.put(AgentExecutorStreamResponse(
                status="error",
                error=str(e),
                response=f"Ocorreu um erro ao executar o agente.\n"
            ))
        finally:
            await dependencies.queue.put(StopAsyncIteration)

    async def stream_response(
        self,
        dependencies: BasicDependencies,
        callback: Optional[Callable[[AgentExecutorResponse], None]] = None
    ) -> AsyncGenerator[AgentExecutorStreamResponse, None]:
        keepalive_interval = 10  # seconds
        asyncio.create_task(self._pump_stream(dependencies, callback))

        while True:
            try:
                item = await asyncio.wait_for(dependencies.queue.get(), timeout=keepalive_interval)
                if item is StopAsyncIteration:
                    break
                yield item
            except asyncio.TimeoutError:
                yield AgentExecutorStreamResponse(
                    status="keepalive", response=""
                )

        yield AgentExecutorStreamResponse(
            status="end_turn", response=""
        )

    @staticmethod
    def get_constructed_chat_history(chat_history: Optional[List[Dict]]) -> List[ModelMessage]:
        if chat_history is not None:
            return ModelMessagesTypeAdapter.validate_python(chat_history)
        return []
