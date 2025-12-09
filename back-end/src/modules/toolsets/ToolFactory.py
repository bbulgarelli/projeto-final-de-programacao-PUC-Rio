import datetime
import json
from typing import Any, Dict, List, Optional, Type, Union
import unicodedata
from uuid import UUID
from urllib.parse import quote

import httpx
from pydantic_ai import RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerSSE, MCPServerStreamableHTTP, ToolResult
from pydantic_ai.toolsets import FunctionToolset
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.chat.AgentExecutor import BasicDependencies
from src.database.session_manager import session_manager_provider
from src.modules.agents.repositories.AgentRepository import get_agent_repository
from src.modules.toolsets.enums.enums import ToolTypeEnum, ToolsetTypeEnum
from src.modules.toolsets.schemas import ToolSchema, ToolsetSchema
from pydantic_ai.tools import Tool as PydanticTool



def create_tool_definition(tool: ToolSchema, input_schema: Dict, output_schema: Optional[Dict] = None) -> Dict:
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": input_schema,
        "outputSchema": output_schema
    }


class WebhookToolFactory:

    def __init__(
        self, tool: ToolSchema
    ):
        self.tool = tool

    def remove_nulls(self, obj):
        """
        Recursively remove keys with null (None) values from dicts/lists.
        """
        if isinstance(obj, dict):
            return {k: self.remove_nulls(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self.remove_nulls(v) for v in obj if v is not None]
        else:
            return obj

    def to_ascii(self, text: str) -> str:
        # Normalize to NFKD form, which separates accents from letters
        normalized = unicodedata.normalize("NFKD", text)
        # Encode to ASCII, ignoring characters that can't be converted, then decode back to str
        return normalized.encode("ascii", "ignore").decode("ascii")

    def create_input_schema(self):
        json_schema = {
            "type": "object",
            "properties": {}
        }
        if self.tool.webhook_path_params_schema:
            json_schema["properties"]["path_params"] = self.remove_nulls(
                self.tool.webhook_path_params_schema)
        if self.tool.webhook_query_params_schema:
            json_schema["properties"]["query_params"] = self.remove_nulls(
                self.tool.webhook_query_params_schema)
        if self.tool.webhook_body_params_schema:
            json_schema["properties"]["body_params"] = self.remove_nulls(
                self.tool.webhook_body_params_schema)
        return json_schema

    def create_tool(self):

        async def tool_function(
            ctx: RunContext[BasicDependencies],
            path_params: Optional[dict] = None,
            query_params: Optional[dict] = None,
            body_params: Optional[dict] = None
        ) -> Dict[str, Any]:
            """Execute the webhook call with the provided arguments."""

            if not self.tool.webhook_url:
                return {"error": f"No webhook URL configured for tool '{self.tool.name}'"}

            final_webhook_url = self.tool.webhook_url
            if path_params is not None:
                for key, value in path_params.items():
                    path_params[key] = quote(value)
                final_webhook_url = final_webhook_url.format(**path_params)

            if query_params is not None:
                params = ""
                for key, value in query_params.items():
                    if value is not None:
                        params += f"{quote(key)}={quote(value)}&"
                final_webhook_url = final_webhook_url + \
                    "?" + params.rstrip("&")

            request_data = None
            if self.tool.webhook_body_params_schema is not None:
                request_data = body_params if body_params is not None else {}

            headers = None
            if self.tool.webhook_auth_header is not None:
                headers = self.tool.webhook_auth_header

            success = False
            error_message = None
            result = None
            response = None
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.request(
                        method=self.tool.webhook_http_method,
                        url=final_webhook_url,
                        json=request_data,
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()

                    success = True
                    try:
                        result = {
                            "result": response.json(),
                            "status_code": response.status_code
                        }
                    except json.JSONDecodeError:
                        result = {
                            "result": response.text,
                            "status_code": response.status_code
                        }

                except httpx.RequestError as e:
                    success = False
                    error_message = f"Request failed: {str(e)}"
                    result = {
                        "error": f"Request failed: {str(e)}"
                    }
                except httpx.HTTPStatusError as e:
                    success = True
                    error_message = f"HTTP {e.response.status_code}: {e.response.text}"
                    result = {
                        "error": f"HTTP {e.response.status_code}: {e.response.text}",
                        "status_code": e.response.status_code
                    }

            return result

        try:
            json_schema = self.create_input_schema()
            return PydanticTool.from_schema(
                function=tool_function,
                name=self.to_ascii(self.tool.name.lower().replace(' ', '_')),
                description=self.tool.description or f"Execute {self.tool.name}",
                json_schema=json_schema,
                takes_ctx=True
            )
        except Exception as e:
            print(e, flush=True)
            raise e

    def _json_schema_to_python_type(self, field_schema: Dict[str, Any]) -> Type:
        """Convert JSON Schema type to Python type."""
        schema_type = field_schema.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        return type_mapping.get(schema_type, str)


class AgentToolFactory:

    def __init__(self, name: str, agent_id: UUID, tool: ToolSchema, description: Optional[str] = None):
        self.name = name
        self.description = description
        self.agent_id = agent_id
        self.tool = tool

    def to_ascii(self, text: str) -> str:
        # Normalize to NFKD form, which separates accents from letters
        normalized = unicodedata.normalize("NFKD", text)
        # Encode to ASCII, ignoring characters that can't be converted, then decode back to str
        return normalized.encode("ascii", "ignore").decode("ascii")

    def create_tool(self):

        async def agent_tool_function(ctx: RunContext[BasicDependencies], query: str) -> str:
            from src.modules.chat.AgentManager import AgentManager
            response = None
            async with session_manager_provider.get_session_manager().session() as session:
                try:
                    from src.modules.chat.AgentManager import get_agent_manager
                    agent_repo = await get_agent_repository(session, self.agent_id)
                    agent_manager = await get_agent_manager(session, agent_repo)
                    response = await agent_manager.get_response(query, [])
                except Exception as e:
                    raise e
            return response.response

        return PydanticTool.from_schema(
            function=agent_tool_function,
            name=self.to_ascii(self.name.lower().replace(' ', '_')),
            description=(self.description) or f"Execute {self.name}",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query that will be used to execute the agent"
                    }
                },
                "required": ["query"]
            },
            takes_ctx=True
        )


class ToolFactory:

    @staticmethod
    def get_pydantic_function_tool(tool: ToolSchema) -> PydanticTool:
        if tool.tool_type == ToolTypeEnum.WEBHOOK:
            webhook_tool = WebhookToolFactory(
                tool=tool
            ).create_tool()
            return webhook_tool
        elif tool.tool_type == ToolTypeEnum.AGENT:
            agent_tool = AgentToolFactory(
                name=tool.name,
                description=tool.description,
                tool=tool,
                agent_id=tool.target_agent_id
            ).create_tool()
            return agent_tool


class ToolsetFactory:

    @staticmethod
    async def get_pydantic_toolset(toolset: ToolsetSchema) -> Union[FunctionToolset, MCPServerStreamableHTTP]:
        if toolset.toolset_type == ToolsetTypeEnum.MCP_SERVER:
            server = MCPServerStreamableHTTP(
                url=toolset.mcp_server_url,
                headers=toolset.mcp_server_auth_header if toolset.mcp_server_auth_header else None
            )
            return server

        elif toolset.toolset_type == ToolsetTypeEnum.CUSTOM:
            return FunctionToolset(
                [ToolFactory.get_pydantic_function_tool(
                    tool) for tool in toolset.tools]
            )