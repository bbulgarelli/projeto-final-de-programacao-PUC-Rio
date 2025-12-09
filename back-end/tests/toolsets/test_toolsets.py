import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

@pytest.fixture
async def toolset_id(client: AsyncClient):
    response = await client.post("/toolsets", json={"name": "Test TS", "description": "Desc", "toolset_type": "CUSTOM"})
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
async def tool_id(client: AsyncClient, toolset_id):
    tool_payload = {
        "name": "Test Tool",
        "description": "Tool Desc",
        "tool_type": "WEBHOOK",
        "webhook_url": "http://example.com",
        "webhook_http_method": "GET"
    }
    response = await client.post(f"/toolsets/{toolset_id}/tools", json=tool_payload)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.mark.asyncio
async def test_create_toolset(client: AsyncClient):
    response = await client.post("/toolsets", json={"name": "Custom TS", "description": "Desc", "toolset_type": "CUSTOM"})
    assert response.status_code == 201
    assert response.json()["name"] == "Custom TS"

@pytest.mark.asyncio
async def test_get_toolset(client: AsyncClient, toolset_id):
    response = await client.get(f"/toolsets/{toolset_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test TS"

@pytest.mark.asyncio
async def test_update_toolset(client: AsyncClient, toolset_id):
    response = await client.patch(f"/toolsets/{toolset_id}", json={"name": "Updated TS"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated TS"

@pytest.mark.asyncio
async def test_list_toolsets(client: AsyncClient, toolset_id):
    response = await client.get("/toolsets")
    assert response.status_code == 200
    assert len(response.json()["toolsets"]) > 0

@pytest.mark.asyncio
async def test_delete_toolset(client: AsyncClient, toolset_id):
    response = await client.delete(f"/toolsets/{toolset_id}")
    assert response.status_code == 204
    
    response = await client.get(f"/toolsets/{toolset_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_tool(client: AsyncClient, toolset_id):
    tool_payload = {
        "name": "My Tool",
        "description": "Tool Desc",
        "tool_type": "WEBHOOK",
        "webhook_url": "http://example.com",
        "webhook_http_method": "GET"
    }
    response = await client.post(f"/toolsets/{toolset_id}/tools", json=tool_payload)
    assert response.status_code == 201
    assert response.json()["name"] == "My Tool"

@pytest.mark.asyncio
async def test_get_tool(client: AsyncClient, tool_id):
    response = await client.get(f"/tools/{tool_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Tool"

@pytest.mark.asyncio
async def test_update_tool(client: AsyncClient, tool_id):
    response = await client.patch(f"/tools/{tool_id}", json={"name": "Updated Tool"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Tool"

@pytest.mark.asyncio
async def test_delete_tool(client: AsyncClient, tool_id):
    response = await client.delete(f"/tools/{tool_id}")
    assert response.status_code == 204
    
    response = await client.get(f"/tools/{tool_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_mcp_toolset(client: AsyncClient, mocker):
    # Mock MCPManager
    mock_manager = AsyncMock()
    mock_manager.setup_mcp.return_value = None
    
    mocker.patch("src.modules.toolsets.routes.MCPManager", return_value=mock_manager)
    
    payload = {
        "name": "MCP Server",
        "toolset_type": "MCP_SERVER",
        "mcp_server_url": "http://mcp.local"
    }
    response = await client.post("/toolsets", json=payload)
    assert response.status_code == 201
    assert response.json()["mcp_server_url"] == "http://mcp.local"
