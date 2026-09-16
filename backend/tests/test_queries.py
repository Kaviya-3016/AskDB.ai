import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_and_execute_query_flow(client: AsyncClient, analyst_auth_token: str):
    headers = {"Authorization": f"Bearer {analyst_auth_token}"}

    # 1. Fetch default schemas
    schemas_resp = await client.get("/api/schemas", headers=headers)
    assert schemas_resp.status_code == 200
    schemas = schemas_resp.json()
    assert len(schemas) > 0
    schema_id = schemas[0]["id"]

    # 2. Generate SQL from natural language prompt
    gen_resp = await client.post(
        "/api/queries/generate",
        json={
            "schema_id": schema_id,
            "prompt": "Show top 5 customers by total spent",
        },
        headers=headers,
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "generated_sql" in gen_data
    assert gen_data["confidence_score"] > 0
    sql = gen_data["generated_sql"]
    query_id = gen_data["query_id"]

    # 3. Validate query
    val_resp = await client.post(
        "/api/queries/validate",
        json={"sql_query": sql},
        headers=headers,
    )
    assert val_resp.status_code == 200
    assert val_resp.json()["is_valid"] is True

    # 4. Explain query
    exp_resp = await client.post(
        "/api/queries/explain",
        json={"sql_query": sql},
        headers=headers,
    )
    assert exp_resp.status_code == 200
    assert len(exp_resp.json()["operations"]) > 0

    # 5. Execute query on sandboxed demo DB
    exec_resp = await client.post(
        "/api/queries/execute",
        json={
            "schema_id": schema_id,
            "sql_query": sql,
            "query_id": query_id,
        },
        headers=headers,
    )
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["status"] == "SUCCESS"
    assert len(exec_data["columns"]) > 0
    assert exec_data["row_count"] > 0
    assert len(exec_data["rows"]) > 0

    # 6. Retrieve results
    res_resp = await client.get(f"/api/results/{query_id}", headers=headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["row_count"] == exec_data["row_count"]

    # 7. Export CSV
    export_resp = await client.post(
        f"/api/results/{query_id}/export",
        json={"format": "csv"},
        headers=headers,
    )
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/csv")
    assert len(export_resp.content) > 0

    # 8. Query History
    hist_resp = await client.get("/api/queries/history", headers=headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) > 0


@pytest.mark.asyncio
async def test_generate_streaming_query_flow(client: AsyncClient, analyst_auth_token: str):
    headers = {"Authorization": f"Bearer {analyst_auth_token}"}

    # 1. Fetch default schemas
    schemas_resp = await client.get("/api/schemas", headers=headers)
    assert schemas_resp.status_code == 200
    schema_id = schemas_resp.json()[0]["id"]

    # 2. Test Stream endpoint
    stream_resp = await client.post(
        "/api/queries/generate/stream",
        json={
            "schema_id": schema_id,
            "prompt": "Show monthly revenue breakdown",
            "model_name": "querycraft-ultra",
        },
        headers=headers,
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    text_content = stream_resp.text
    assert "data: {" in text_content
    assert '"type": "token"' in text_content
    assert '"type": "complete"' in text_content

