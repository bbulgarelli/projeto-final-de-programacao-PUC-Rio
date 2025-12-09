import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_get_agent(client: AsyncClient):
    payload = {
        "name": "Test Agent",
        "description": "A test agent",
        "prompt": "You are a test agent",
        "contextualize_system_prompt": "Contextualize",
        "enum_model": "chatgpt_3_5_turbo",
        "max_response_tokens": 1000,
        "temperature": 0.5,
        "history_message_count": 5
    }
    response = await client.post("/agents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data
    
    agent_id = data["id"]
    
    # Get agent
    response = await client.get(f"/agents/{agent_id}")
    assert response.status_code == 200
    assert response.json()["id"] == agent_id

@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    response = await client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert "total_agents" in data
    assert isinstance(data["agents"], list)

@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    # Create agent first
    payload = {
        "name": "Update Test Agent",
        "prompt": "Original prompt",
        "contextualize_system_prompt": "Original context"
    }
    create_res = await client.post("/agents", json=payload)
    agent_id = create_res.json()["id"]
    
    update_payload = {
        "name": "Updated Name",
        "prompt": "Updated prompt"
    }
    response = await client.patch(f"/agents/{agent_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["prompt"] == "Updated prompt"
    assert data["contextualize_system_prompt"] == "Original context"

@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    # Create agent first
    payload = {
        "name": "Delete Test Agent",
        "prompt": "To be deleted",
        "contextualize_system_prompt": "..."
    }
    create_res = await client.post("/agents", json=payload)
    agent_id = create_res.json()["id"]
    
    response = await client.delete(f"/agents/{agent_id}")
    assert response.status_code == 204
    
    # Verify deletion
    response = await client.get(f"/agents/{agent_id}")
    assert response.status_code == 404

