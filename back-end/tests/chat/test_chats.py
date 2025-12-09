import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
async def chat_id(client: AsyncClient):
    response = await client.post("/chats", json={"title": "Test Chat"})
    assert response.status_code == 201
    return response.json()["id"]

@pytest.mark.asyncio
async def test_create_chat(client: AsyncClient):
    response = await client.post("/chats", json={"title": "My Chat"})
    assert response.status_code == 201
    assert response.json()["title"] == "My Chat"
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_get_chat(client: AsyncClient, chat_id):
    response = await client.get(f"/chats/{chat_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Chat"

@pytest.mark.asyncio
async def test_update_chat(client: AsyncClient, chat_id):
    response = await client.patch(f"/chats/{chat_id}", json={"title": "Updated Chat"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Chat"

@pytest.mark.asyncio
async def test_list_chats(client: AsyncClient, chat_id):
    response = await client.get("/chats")
    assert response.status_code == 200
    assert len(response.json()["chats"]) > 0

@pytest.mark.asyncio
async def test_delete_chat(client: AsyncClient, chat_id):
    response = await client.delete(f"/chats/{chat_id}")
    assert response.status_code == 204
    
    # Verify Delete
    response = await client.get(f"/chats/{chat_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_ask_question(client: AsyncClient, mocker):
    # Create chat
    chat_res = await client.post("/chats", json={"title": "Q&A Chat"})
    assert chat_res.status_code == 201
    chat_id = chat_res.json()["id"]
    
    # Create agent
    agent_res = await client.post("/agents", json={
        "name": "Q&A Agent",
        "prompt": "You answer questions",
        "contextualize_system_prompt": "Ctx",
        "enum_model": "chatgpt_3_5_turbo",
        "max_response_tokens": 100,
        "temperature": 0.7,
        "history_message_count": 5
    })
    assert agent_res.status_code == 201
    agent_id = agent_res.json()["id"]
    
    # Mock get_agent_manager
    mock_manager = AsyncMock()
    mock_result = MagicMock()
    mock_result.response = "This is a mocked answer."
    mock_result.message_history = []
    mock_manager.get_response.return_value = mock_result
    
    mocker.patch("src.modules.chat.routes.get_agent_manager", return_value=mock_manager)

    # Ask question
    payload = {
        "question": "What is the meaning of life?",
        "agent_id": agent_id
    }
    response = await client.post(f"/chats/{chat_id}/messages", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["response"] == "This is a mocked answer."
    assert data["message"] == "What is the meaning of life?"
