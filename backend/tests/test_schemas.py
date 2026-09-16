import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_schema_lifecycle(client: AsyncClient, analyst_auth_token: str):
    headers = {"Authorization": f"Bearer {analyst_auth_token}"}

    # Upload custom schema
    custom_ddl = """
    CREATE TABLE employees (
        emp_id INT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        department VARCHAR(50),
        salary NUMERIC(10, 2)
    );
    """
    upload_resp = await client.post(
        "/api/schemas/upload",
        json={
            "name": "HR Department DB",
            "description": "Employee database",
            "dialect": "postgres",
            "ddl_content": custom_ddl,
        },
        headers=headers,
    )
    assert upload_resp.status_code == 201
    created_schema = upload_resp.json()
    assert created_schema["name"] == "HR Department DB"
    schema_id = created_schema["id"]

    # Fetch tables
    tables_resp = await client.get(f"/api/schemas/{schema_id}/tables", headers=headers)
    assert tables_resp.status_code == 200
    tables = tables_resp.json()
    assert len(tables) == 1
    assert tables[0]["name"] == "employees"


@pytest.mark.asyncio
async def test_table_preview(client: AsyncClient, analyst_auth_token: str):
    headers = {"Authorization": f"Bearer {analyst_auth_token}"}
    preview_resp = await client.get("/api/schemas/1/preview?table_name=customers&limit=5", headers=headers)
    assert preview_resp.status_code == 200
    data = preview_resp.json()
    assert data["table_name"] == "customers"
    assert len(data["sample_rows"]) > 0
    assert data["total_row_count"] > 0
