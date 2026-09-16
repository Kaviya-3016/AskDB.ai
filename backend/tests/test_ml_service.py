import pytest
from app.ml.model_service import model_service
from app.ml.tokenizer import prompt_builder
from app.ml.explainer import explainer


@pytest.mark.asyncio
async def test_model_generation_top_customers():
    schema_json = '{"tables": [{"name": "customers", "columns": [{"name": "customer_id", "type": "INT"}, {"name": "first_name", "type": "TEXT"}]}]}'
    prompt = "Show me the top 5 customers by total spend"
    
    result = await model_service.generate_sql(
        schema_id=1,
        schema_json_str=schema_json,
        user_prompt=prompt,
    )
    assert result["generated_sql"] is not None
    assert "SELECT" in result["generated_sql"]
    assert result["confidence_score"] >= 0.8
    assert result["inference_time_ms"] > 0
    assert "bar" in result["suggested_charts"] or "table" in result["suggested_charts"]


def test_sql_explainer():
    sql = "SELECT country, COUNT(customer_id) AS total_cust FROM customers WHERE account_status = 'ACTIVE' GROUP BY country ORDER BY total_cust DESC LIMIT 10;"
    explanation = explainer.explain_query(sql)
    assert "customers" in explanation.tables_involved
    assert len(explanation.operations) > 0
    assert any("COUNT" in agg for agg in explanation.aggregations)
