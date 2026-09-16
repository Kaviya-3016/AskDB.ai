import pytest
from httpx import AsyncClient
import io


@pytest.mark.asyncio
async def test_dataset_upload_and_query_flow(client: AsyncClient):
    # 1. Prepare sample CSV
    csv_data = (
        "patient_id,patient_name,age,gender,diagnosis,billing_amount,admission_days\n"
        "1,Alice Green,45,Female,Hypertension,1250.50,3\n"
        "2,Bob White,58,Male,Type 2 Diabetes,3400.00,7\n"
        "3,Charlie Brown,32,Male,Asthma,850.00,2\n"
        "4,Diana Prince,67,Female,Pneumonia,5200.75,10\n"
        "5,Evan Wright,29,Male,Appendicitis,4100.20,4\n"
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    # 2. Upload dataset via API
    files = {"file": ("hospital_patients.csv", file_bytes, "text/csv")}
    data = {
        "dataset_name": "Hospital Inpatient Records",
        "table_name": "hospital_patients",
    }

    res = await client.post("/api/schemas/upload-dataset", files=files, data=data)
    assert res.status_code == 201
    upload_res = res.json()
    assert upload_res["table_name"] == "hospital_patients"
    assert upload_res["row_count"] == 5
    schema_id = upload_res["schema_id"]

    # 3. Generate SQL from natural language prompt for the uploaded dataset
    gen_res = await client.post(
        "/api/queries/generate",
        json={
            "schema_id": schema_id,
            "prompt": "Show total billing_amount by diagnosis",
        },
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "hospital_patients" in gen_data["generated_sql"]
    assert "diagnosis" in gen_data["generated_sql"]

    # 4. Execute the dynamically generated SQL on the live ingested table
    exec_res = await client.post(
        "/api/queries/execute",
        json={
            "schema_id": schema_id,
            "sql_query": gen_data["generated_sql"],
            "natural_language_query": "Show total billing_amount by diagnosis",
        },
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "SUCCESS"
    assert exec_data["row_count"] > 0
    assert len(exec_data["rows"]) > 0
