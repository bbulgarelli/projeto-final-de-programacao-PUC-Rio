import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.fixture
async def kb_id(client: AsyncClient):
    response = await client.post("/knowledge-bases", json={"name": "Test KB", "description": "Test Desc"})
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
async def file_id(client: AsyncClient, kb_id, mocker):
    mocker.patch("src.modules.knowledge_base.routes.process_file_bg_task")
    files = {"file": ("test.txt", b"content", "text/plain")}
    response = await client.post(f"/knowledge-bases/{kb_id}/files", files=files)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.mark.asyncio
async def test_create_knowledge_base(client: AsyncClient):
    response = await client.post("/knowledge-bases", json={"name": "KB 1", "description": "Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "KB 1"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_knowledge_base(client: AsyncClient, kb_id):
    response = await client.get(f"/knowledge-bases/{kb_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test KB"

@pytest.mark.asyncio
async def test_update_knowledge_base(client: AsyncClient, kb_id):
    response = await client.patch(f"/knowledge-bases/{kb_id}", json={"name": "KB Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "KB Updated"

@pytest.mark.asyncio
async def test_list_knowledge_bases(client: AsyncClient, kb_id):
    response = await client.get("/knowledge-bases")
    assert response.status_code == 200
    assert len(response.json()["knowledge_bases"]) > 0

@pytest.mark.asyncio
async def test_delete_knowledge_base(client: AsyncClient, kb_id):
    response = await client.delete(f"/knowledge-bases/{kb_id}")
    assert response.status_code == 204
    
    response = await client.get(f"/knowledge-bases/{kb_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_upload_file(client: AsyncClient, kb_id, mocker):
    mocker.patch("src.modules.knowledge_base.routes.process_file_bg_task")
    files = {"file": ("new_test.txt", b"new content", "text/plain")}
    response = await client.post(f"/knowledge-bases/{kb_id}/files", files=files)
    assert response.status_code == 201
    assert response.json()["name"] == "new_test.txt"

@pytest.mark.asyncio
async def test_get_file(client: AsyncClient, file_id):
    response = await client.get(f"/files/{file_id}")
    assert response.status_code == 200
    assert "name" in response.json()

@pytest.mark.asyncio
async def test_list_files_for_knowledge_base(client: AsyncClient, kb_id, file_id):
    response = await client.get(f"/knowledge-bases/{kb_id}/files")
    assert response.status_code == 200
    assert len(response.json()["files"]) > 0

@pytest.mark.asyncio
async def test_update_file(client: AsyncClient, file_id):
    response = await client.patch(f"/files/{file_id}", json={"name": "updated.txt"})
    assert response.status_code == 200
    assert response.json()["name"] == "updated.txt"

@pytest.mark.asyncio
async def test_delete_file(client: AsyncClient, file_id):
    response = await client.delete(f"/files/{file_id}")
    assert response.status_code == 204
    
    response = await client.get(f"/files/{file_id}")
    assert response.status_code == 404
