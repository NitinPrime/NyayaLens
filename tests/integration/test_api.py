"""API integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "nyayalens-api"


@pytest.mark.asyncio
async def test_create_case(client):
    response = await client.post(
        "/cases",
        json={
            "description": "I lent my friend ₹80,000 through UPI. He promised repayment in three months but has refused after six months."
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["description"].startswith("I lent")


@pytest.mark.asyncio
async def test_create_case_validation_error(client):
    response = await client.post("/cases", json={"description": "short"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_case_flow(client):
    create_response = await client.post(
        "/cases",
        json={
            "description": "I purchased a defective laptop for ₹65,000. The seller refused a refund despite the invoice and email correspondence."
        },
    )
    assert create_response.status_code == 201
    case_id = create_response.json()["id"]

    analyze_response = await client.post(f"/cases/{case_id}/analyze")
    assert analyze_response.status_code == 202
    analysis = analyze_response.json()
    assert analysis["status"] == "completed"
    assert "disclaimer" in analysis
    assert len(analysis["issues"]) >= 1
    assert "claimant_argument" in analysis
    assert "respondent_argument" in analysis
    assert analysis["overall_confidence"] in {"high", "medium", "low", "insufficient_evidence"}

    get_response = await client.get(f"/cases/{case_id}")
    assert get_response.status_code == 200
    case_data = get_response.json()
    assert len(case_data["parties"]) >= 1
    assert len(case_data["facts"]) >= 1


@pytest.mark.asyncio
async def test_legal_search_and_chat(client):
    search = await client.post("/api/v1/legal/search", json={"query": "security deposit landlord refund"})
    assert search.status_code == 200
    assert isinstance(search.json(), list)

    created = await client.post(
        "/api/v1/cases",
        json={
            "description": "My landlord refuses to return my ₹50,000 security deposit even though I moved out and there is no damage."
        },
    )
    case_id = created.json()["id"]
    await client.post(f"/api/v1/cases/{case_id}/analyze")
    chat = await client.post(
        f"/api/v1/cases/{case_id}/messages",
        json={"message": "What evidence should I collect?"},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["message"]["role"] == "assistant"
    assert "content" in body["message"]
