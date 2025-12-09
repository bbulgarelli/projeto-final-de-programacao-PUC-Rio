import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_available_models(client: AsyncClient):
    response = await client.get("/available-models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "model_key" in data[0]
    assert "name" in data[0]

