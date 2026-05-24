from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models import PersonaTrait, Project


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, db_session):
    response = await client.post(
        "/api/v1/projects",
        json={"name": "测试项目", "description": "用于测试"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试项目"
    assert data["description"] == "用于测试"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, db_session):
    project = Project(id="list-test-1", name="列表测试项目", description="测试")
    db_session.add(project)
    await db_session.commit()

    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, db_session):
    response = await client.get("/api/v1/projects/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_persona_trait(client: AsyncClient, db_session):
    project = Project(id="trait-proj-1", name="Trait项目", description="测试")
    db_session.add(project)
    await db_session.commit()

    response = await client.post(
        "/api/v1/persona/traits",
        json={
            "category": "occupation",
            "label": "程序员",
            "weight": 1.0,
            "scope": "public",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "occupation"
    assert data["label"] == "程序员"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient, db_session):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data
