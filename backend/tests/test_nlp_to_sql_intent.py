import pytest
import sqlite3
import json
from app.ml.model_service import model_service
from app.ml.intent import intent_analyzer, QueryIntent
from app.ml.semantic_validator import semantic_validator
from app.ml.validator import validator


WEATHER_SCHEMA_JSON = json.dumps({
    "tables": [{
        "name": "seattle_weather",
        "columns": [
            {"name": "date", "type": "VARCHAR(255)"},
            {"name": "precipitation", "type": "NUMERIC(10,2)"},
            {"name": "temp_max", "type": "NUMERIC(10,2)"},
            {"name": "temp_min", "type": "NUMERIC(10,2)"},
            {"name": "wind", "type": "NUMERIC(10,2)"},
            {"name": "weather", "type": "VARCHAR(255)"}
        ]
    }]
})

schema_tables = json.loads(WEATHER_SCHEMA_JSON)["tables"]


def get_demo_db_conn():
    # Use real demo database with 1461 seattle_weather rows
    return sqlite3.connect("demo_ecommerce.db")


# =============================================================================
# 1. DIRECT LOOKUP TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_direct_lookup_jan_1_2012():
    prompt = "Show the weather on January 1, 2012."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.DIRECT_LOOKUP.value
    assert "WHERE" in sql.upper()
    assert "2012-01-01" in sql
    assert "GROUP BY" not in sql.upper()
    assert "COUNT" not in sql.upper()
    assert "SUM(" not in sql.upper()
    assert res["confidence_score"] >= 0.90
    assert res["is_valid"] is True

    # Execution check
    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert "drizzle" in str(rows[0]).lower()


@pytest.mark.asyncio
async def test_direct_lookup_march_15_2015():
    prompt = "What was the weather on March 15, 2015?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.DIRECT_LOOKUP.value
    assert "2015-03-15" in sql
    assert "GROUP BY" not in sql.upper()
    assert res["confidence_score"] >= 0.90

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert "rain" in str(rows[0]).lower()


@pytest.mark.asyncio
async def test_direct_lookup_iso_date():
    prompt = "Show me the weather for 2014-06-20."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.DIRECT_LOOKUP.value
    assert "2014-06-20" in sql
    assert "GROUP BY" not in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1


# =============================================================================
# 2. EQUALITY FILTERS
# =============================================================================

@pytest.mark.asyncio
async def test_equality_filter_drizzle():
    prompt = "Show records where weather was drizzle."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.FILTER_LIST.value
    assert "weather" in sql.lower()
    assert "drizzle" in sql.lower()
    assert "GROUP BY" not in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0
    for r in rows:
        assert "drizzle" in [str(item).lower() for item in r]


@pytest.mark.asyncio
async def test_equality_filter_orders_completed():
    ecommerce_schema = json.dumps({
        "tables": [{
            "name": "orders",
            "columns": [
                {"name": "order_id", "type": "INT"},
                {"name": "status", "type": "VARCHAR"},
                {"name": "total_amount", "type": "NUMERIC"}
            ]
        }]
    })
    prompt = "List orders where status is COMPLETED"
    res = await model_service.generate_sql(1, ecommerce_schema, prompt)
    sql = res["generated_sql"]
    assert "orders" in sql.lower()
    assert "status" in sql.lower()


# =============================================================================
# 3. NUMERIC FILTERS
# =============================================================================

@pytest.mark.asyncio
async def test_numeric_filter_precipitation_greater_than_20():
    prompt = "Show days when precipitation was greater than 20."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.FILTER_LIST.value
    assert "precipitation > 20" in sql or "precipitation > 20.0" in sql
    assert "GROUP BY" not in sql.upper()
    assert res["confidence_score"] >= 0.90

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0
    # Every returned precipitation must be > 20
    for r in rows:
        # Check column index of precipitation (index 1)
        assert r[1] > 20


@pytest.mark.asyncio
async def test_numeric_filter_wind_less_than_2():
    prompt = "Show days where wind was less than 2."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.FILTER_LIST.value
    assert "wind < 2" in sql or "wind < 2.0" in sql

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0


# =============================================================================
# 4. DATE FILTERS
# =============================================================================

@pytest.mark.asyncio
async def test_date_filter_month_year():
    prompt = "Show weather data for November 2013."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "2013-11%" in sql or "2013-11" in sql
    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 30  # 30 days in November


@pytest.mark.asyncio
async def test_date_filter_entire_year():
    prompt = "Show weather in 2014."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "2014%" in sql or "2014" in sql
    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 365  # 365 days in 2014


# =============================================================================
# 5. DATE RANGES
# =============================================================================

@pytest.mark.asyncio
async def test_date_range_jan_1_to_jan_10():
    prompt = "Show the weather between January 1 and January 10, 2012."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.DATE_RANGE.value
    assert "BETWEEN" in sql.upper() or (">=" in sql and "<=" in sql)
    assert "2012-01-01" in sql
    assert "2012-01-10" in sql
    assert res["confidence_score"] >= 0.90

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 10


@pytest.mark.asyncio
async def test_date_range_iso_between():
    prompt = "Weather between 2013-05-01 and 2013-05-07."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.DATE_RANGE.value
    assert "2013-05-01" in sql
    assert "2013-05-07" in sql

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 7


# =============================================================================
# 6. AGGREGATION
# =============================================================================

@pytest.mark.asyncio
async def test_aggregation_avg_temp_max():
    prompt = "What is the average maximum temperature?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.AGGREGATION.value
    assert "AVG(" in sql.upper()
    assert "temp_max" in sql.lower()
    assert "GROUP BY" not in sql.upper()
    assert res["confidence_score"] >= 0.90

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] > 10.0


@pytest.mark.asyncio
async def test_aggregation_rainy_days_count():
    prompt = "How many rainy days were there?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.AGGREGATION.value
    assert "COUNT(" in sql.upper()
    assert "weather" in sql.lower()
    assert "rain" in sql.lower()
    assert "GROUP BY" not in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 641


@pytest.mark.asyncio
async def test_aggregation_total_precipitation():
    prompt = "What was the total precipitation?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.AGGREGATION.value
    assert "SUM(" in sql.upper()
    assert "precipitation" in sql.lower()
    assert "GROUP BY" not in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] > 1000.0


@pytest.mark.asyncio
async def test_aggregation_min_temperature():
    prompt = "What was the minimum temperature recorded?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.AGGREGATION.value
    assert "MIN(" in sql.upper()
    assert "temp_min" in sql.lower()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] < 0.0  # Seattle winter min temp


# =============================================================================
# 7. GROUP BY
# =============================================================================

@pytest.mark.asyncio
async def test_groupby_weather_condition():
    prompt = "What was the average temperature for each weather condition?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.GROUPING.value
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()
    assert "AVG(" in sql.upper()
    assert res["confidence_score"] >= 0.90

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 5  # drizzle, fog, rain, snow, sun


@pytest.mark.asyncio
async def test_groupby_month_rainy_days():
    prompt = "Which month had the most rainy days?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] in [QueryIntent.COMPARATIVE_AGGREGATION.value, QueryIntent.GROUPING.value]
    assert "GROUP BY" in sql.upper()
    assert "ORDER BY" in sql.upper()
    assert "LIMIT 1" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "2015-12"
    assert rows[0][1] == 25


@pytest.mark.asyncio
async def test_groupby_explicit_group_clause():
    prompt = "Count of records grouped by weather."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.GROUPING.value
    assert "GROUP BY" in sql.upper()
    assert "COUNT(" in sql.upper()


# =============================================================================
# 8. SORTING
# =============================================================================

@pytest.mark.asyncio
async def test_sorting_temperature_asc():
    prompt = "Sort days by temperature ascending."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "ORDER BY" in sql.upper()
    assert "ASC" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0


@pytest.mark.asyncio
async def test_sorting_precipitation_desc():
    prompt = "Order days by precipitation descending."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "ORDER BY" in sql.upper()
    assert "DESC" in sql.upper()
    assert "precipitation" in sql.lower()


# =============================================================================
# 9. TOP-N
# =============================================================================

@pytest.mark.asyncio
async def test_top_n_hottest_day():
    prompt = "What was the hottest day?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.TOP_N.value
    assert "ORDER BY" in sql.upper()
    assert "DESC" in sql.upper()
    assert "LIMIT 1" in sql.upper()
    assert "temp_max" in sql.lower()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "2014-08-11"


@pytest.mark.asyncio
async def test_top_n_10_highest_precipitation():
    prompt = "Show the 10 days with the highest precipitation."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.TOP_N.value
    assert "ORDER BY" in sql.upper()
    assert "LIMIT 10" in sql.upper()
    assert "precipitation" in sql.lower()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 10
    # Highest precipitation in dataset is 55.9
    assert rows[0][1] == 55.9


@pytest.mark.asyncio
async def test_top_n_coldest_day():
    prompt = "What was the coldest day?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.TOP_N.value
    assert "ORDER BY" in sql.upper()
    assert "ASC" in sql.upper()
    assert "LIMIT 1" in sql.upper()
    assert "temp_min" in sql.lower()


# =============================================================================
# 10. MULTIPLE CONDITIONS
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_conditions_rain_and_precip():
    prompt = "Show days with rain where precipitation was greater than 10."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "rain" in sql.lower()
    assert "precipitation > 10" in sql or "precipitation > 10.0" in sql
    assert "AND" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0


@pytest.mark.asyncio
async def test_multiple_conditions_precip_and_wind():
    prompt = "Days where precipitation was greater than 15 and wind was greater than 5."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "precipitation > 15" in sql or "precipitation > 15.0" in sql
    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0


# =============================================================================
# 11. COMPARISON QUESTIONS
# =============================================================================

@pytest.mark.asyncio
async def test_comparison_avg_temp_by_condition():
    prompt = "Compare average temperature by weather condition."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.GROUPING.value
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()


@pytest.mark.asyncio
async def test_comparison_precipitation_by_condition():
    prompt = "Compare precipitation across weather conditions."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()


# =============================================================================
# 12. AMBIGUOUS QUESTIONS
# =============================================================================

@pytest.mark.asyncio
async def test_ambiguous_weather_info():
    prompt = "Weather info"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    # Ambiguous prompt should default to safe simple select without hallucinated GROUP BY
    assert "GROUP BY" not in sql.upper()
    assert "seattle_weather" in sql.lower()


@pytest.mark.asyncio
async def test_ambiguous_seattle_days():
    prompt = "Seattle days"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert "GROUP BY" not in sql.upper()
    assert "seattle_weather" in sql.lower()


# =============================================================================
# 13. UNSUPPORTED QUESTIONS
# =============================================================================

@pytest.mark.asyncio
async def test_unsupported_president():
    prompt = "Who was the president of the United States in 2012?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["intent"] == QueryIntent.UNSUPPORTED.value
    assert res["confidence_score"] <= 0.35


@pytest.mark.asyncio
async def test_unsupported_poem():
    prompt = "Write a poem about Seattle rain."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["intent"] == QueryIntent.UNSUPPORTED.value
    assert res["confidence_score"] <= 0.35


# =============================================================================
# 14. SQL INJECTION ATTEMPTS
# =============================================================================

@pytest.mark.asyncio
async def test_injection_drop_table():
    prompt = "'; DROP TABLE seattle_weather; --"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["intent"] == QueryIntent.INJECTION_ATTEMPT.value
    assert res["confidence_score"] == 0.0
    assert "DROP TABLE" not in res["generated_sql"].upper() or "BLOCKED" in res["generated_sql"].upper()


@pytest.mark.asyncio
async def test_injection_delete_from():
    prompt = "Show weather; DELETE FROM seattle_weather WHERE 1=1;"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["confidence_score"] == 0.0 or "DELETE FROM" not in res["generated_sql"].upper()


# =============================================================================
# 15. QUESTIONS UNRELATED TO DATABASE
# =============================================================================

@pytest.mark.asyncio
async def test_unrelated_capital_of_france():
    prompt = "What is the capital of France?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["intent"] == QueryIntent.UNSUPPORTED.value
    assert res["confidence_score"] <= 0.35


@pytest.mark.asyncio
async def test_unrelated_recipe():
    prompt = "How to bake a chocolate cake?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)

    assert res["intent"] == QueryIntent.UNSUPPORTED.value
    assert res["confidence_score"] <= 0.35


# =============================================================================
# 16. SEMANTIC VALIDATOR REJECTION TEST
# =============================================================================

def test_semantic_validator_rejects_incorrect_aggregation():
    prompt = "Show the weather on January 1, 2012."
    bad_sql = """SELECT weather, COUNT(*) AS total_records, ROUND(SUM(precipitation), 2) AS total_precipitation
FROM seattle_weather
GROUP BY weather
ORDER BY total_precipitation DESC
LIMIT 25;"""

    intent_res = intent_analyzer.analyze(prompt, schema_tables)
    res = semantic_validator.validate(bad_sql, intent_res, schema_tables)

    assert res.is_valid is False
    assert res.semantic_score < 0.50
    assert any("GROUP BY" in issue for issue in res.issues)
    assert any("aggregation" in issue.lower() for issue in res.issues)


# =============================================================================
# 16. COMPARATIVE AGGREGATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_comparative_aggregation_highest_avg_max_temp():
    prompt = "Which weather condition had the highest average maximum temperature?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.COMPARATIVE_AGGREGATION.value
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()
    assert "ORDER BY" in sql.upper()
    assert "DESC" in sql.upper()
    assert "LIMIT 1" in sql.upper()
    assert res["confidence_score"] >= 0.95

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "sun"
    assert rows[0][1] == 19.86


@pytest.mark.asyncio
async def test_comparative_aggregation_lowest_avg_max_temp():
    prompt = "Which weather condition had the lowest average maximum temperature?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.COMPARATIVE_AGGREGATION.value
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()
    assert "ORDER BY" in sql.upper()
    assert "ASC" in sql.upper()
    assert "LIMIT 1" in sql.upper()
    assert res["confidence_score"] >= 0.95

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "snow"
    assert rows[0][1] == 5.57


@pytest.mark.asyncio
async def test_comparative_aggregation_highest_wind_speed():
    prompt = "Which weather condition had the highest wind speed?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.COMPARATIVE_AGGREGATION.value
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()
    assert "ORDER BY" in sql.upper()
    assert "DESC" in sql.upper()
    assert "LIMIT 1" in sql.upper()


@pytest.mark.asyncio
async def test_comparative_aggregation_month_highest_avg_temp():
    prompt = "Which month had the highest average maximum temperature?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["intent"] == QueryIntent.COMPARATIVE_AGGREGATION.value
    assert "GROUP BY" in sql.upper()
    assert "month" in sql.lower()
    assert "ORDER BY" in sql.upper()
    assert "LIMIT 1" in sql.upper()


def test_semantic_validator_rejects_missing_groupby_on_comparative_question():
    prompt = "Which weather condition had the highest average maximum temperature?"
    bad_sql = "SELECT ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather;"

    intent_res = intent_analyzer.analyze(prompt, schema_tables)
    assert intent_res.intent == QueryIntent.COMPARATIVE_AGGREGATION

    res = semantic_validator.validate(bad_sql, intent_res, schema_tables)

    assert res.is_valid is False
    assert res.semantic_score < 0.50
    assert any("Missing GROUP BY" in issue for issue in res.issues)
    assert any("Missing ORDER BY" in issue for issue in res.issues)
    assert any("Missing LIMIT" in issue for issue in res.issues)


# =============================================================================
# 13. CONSTRAINT PRESERVATION & COMPOSITE QUERY PLANNING TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_composite_5_days_highest_precipitation_during_2012():
    prompt = "Show the 5 days with the highest precipitation during 2012."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert res["confidence_score"] >= 0.90
    assert "2012-01-01" in sql
    assert "2013-01-01" in sql
    assert "ORDER BY" in sql.upper()
    assert "precipitation" in sql.lower()
    assert "DESC" in sql.upper()
    assert "LIMIT 5" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 5
    for r in rows:
        date_val = str(r[0])
        assert date_val.startswith("2012"), f"Row date {date_val} is not in 2012"


@pytest.mark.asyncio
async def test_composite_10_rainiest_days_in_2015():
    prompt = "Show the 10 rainiest days in 2015."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "2015" in sql
    assert "ORDER BY" in sql.upper()
    assert "precipitation" in sql.lower()
    assert "DESC" in sql.upper()
    assert "LIMIT 10" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 10
    for r in rows:
        date_val = str(r[0])
        assert date_val.startswith("2015"), f"Row date {date_val} is not in 2015"


@pytest.mark.asyncio
async def test_composite_5_coldest_days_in_2013():
    prompt = "Show the 5 coldest days in 2013."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "2013" in sql
    assert "ORDER BY" in sql.upper()
    assert "temp_min" in sql.lower()
    assert "ASC" in sql.upper()
    assert "LIMIT 5" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 5
    for r in rows:
        date_val = str(r[0])
        assert date_val.startswith("2013"), f"Row date {date_val} is not in 2013"


@pytest.mark.asyncio
async def test_composite_10_hottest_rainy_days_in_2014():
    prompt = "Show the 10 hottest rainy days in 2014."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "2014" in sql
    assert "rain" in sql.lower()
    assert "ORDER BY" in sql.upper()
    assert "temp_max" in sql.lower()
    assert "DESC" in sql.upper()
    assert "LIMIT 10" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 10
    for r in rows:
        date_val = str(r[0])
        weather_val = str(r[-1]).lower()
        assert date_val.startswith("2014"), f"Row date {date_val} is not in 2014"
        assert "rain" in weather_val, f"Weather {weather_val} is not rain"


@pytest.mark.asyncio
async def test_composite_5_days_lowest_wind_during_2012():
    prompt = "Show the 5 days with the lowest wind speed during 2012."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "2012" in sql
    assert "ORDER BY" in sql.upper()
    assert "wind" in sql.lower()
    assert "ASC" in sql.upper()
    assert "LIMIT 5" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 5
    for r in rows:
        date_val = str(r[0])
        assert date_val.startswith("2012"), f"Row date {date_val} is not in 2012"


@pytest.mark.asyncio
async def test_composite_avg_temp_rainy_days_in_2012():
    prompt = "What was the average maximum temperature during rainy days in 2012?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "AVG(" in sql.upper()
    assert "temp_max" in sql.lower()
    assert "rain" in sql.lower()
    assert "2012" in sql

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] is not None
    assert rows[0][0] > 0.0


@pytest.mark.asyncio
async def test_composite_highest_avg_max_temp_condition_in_2012():
    prompt = "Which weather condition had the highest average maximum temperature in 2012?"
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "GROUP BY" in sql.upper()
    assert "weather" in sql.lower()
    assert "AVG(" in sql.upper()
    assert "2012" in sql
    assert "ORDER BY" in sql.upper()
    assert "LIMIT 1" in sql.upper()

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] in ["fog", "sun"]
    assert rows[0][1] is not None


@pytest.mark.asyncio
async def test_composite_rainy_days_precipitation_above_10_during_2012():
    prompt = "Show rainy days with precipitation above 10 during 2012."
    res = await model_service.generate_sql(2, WEATHER_SCHEMA_JSON, prompt)
    sql = res["generated_sql"]

    assert res["is_valid"] is True
    assert "rain" in sql.lower()
    assert "10" in sql
    assert "2012" in sql

    conn = get_demo_db_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    assert len(rows) > 0
    for r in rows:
        assert str(r[0]).startswith("2012")


def test_constraint_completeness_validator_flags_dropped_date_constraint():
    prompt = "Show the 5 days with the highest precipitation during 2012."
    dropped_constraint_sql = """
    SELECT date, precipitation, weather
    FROM seattle_weather
    ORDER BY precipitation DESC
    LIMIT 5;
    """

    intent_res = intent_analyzer.analyze(prompt, schema_tables)
    assert len(intent_res.date_filters) > 0, "Intent analyzer must detect date filter for 2012"

    sem_res = semantic_validator.validate(dropped_constraint_sql, intent_res, schema_tables)

    assert sem_res.is_valid is False
    assert sem_res.semantic_score <= 0.35
    assert any("Constraint completeness failed" in issue for issue in sem_res.issues)
    assert any("date filter" in issue for issue in sem_res.issues)


