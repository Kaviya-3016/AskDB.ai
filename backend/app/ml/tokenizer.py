import json
from typing import Dict, Any, List, Optional


FEW_SHOT_GUIDANCE = """
### CORE GENERATION PRINCIPLES:
1. Answer ONLY the user's specific question. Do NOT assume or invent extra analytical requirements.
2. Do NOT add aggregation (COUNT, SUM, AVG, MIN, MAX) unless explicitly asked.
3. Do NOT add GROUP BY unless required by explicit phrasing (e.g., 'for each', 'by category', 'per month').
4. Do NOT add ORDER BY unless requested or logically required (e.g., 'highest', 'top 10', 'latest').
5. Do NOT add an arbitrary LIMIT unless requested or logically necessary.
6. Prefer the simplest valid SQL query that directly answers the question.
7. Use ONLY tables and columns present in the provided schema.
8. Preserve explicit filters such as dates, values, and categories precisely.
9. Map natural dates to ISO date format 'YYYY-MM-DD' (e.g. 'January 1, 2012' -> '2012-01-01').
10. NEVER substitute a different analytical question for the user's actual question.

### POSITIVE & NEGATIVE EXAMPLES:
- Example 1 (Direct Lookup):
  User Question: "Show the weather on January 1, 2012."
  CORRECT:
    SELECT weather FROM seattle_weather WHERE date = '2012-01-01';
  INCORRECT:
    SELECT weather, COUNT(*) FROM seattle_weather GROUP BY weather;
  Reason: The incorrect query groups and counts across all records, answering an aggregation question instead of finding the single requested day's weather.

- Example 2 (Direct Lookup with Date):
  User Question: "What was the weather on March 15, 2015?"
  CORRECT:
    SELECT weather FROM seattle_weather WHERE date = '2015-03-15';
  INCORRECT:
    SELECT weather, COUNT(*) AS total_records FROM seattle_weather GROUP BY weather ORDER BY total_records DESC LIMIT 25;
  Reason: Adding GROUP BY and COUNT completely alters the user's intent from row lookup to category frequency.

- Example 3 (Filtered Condition):
  User Question: "Show days when precipitation was greater than 20."
  CORRECT:
    SELECT date, precipitation, weather FROM seattle_weather WHERE precipitation > 20;
  INCORRECT:
    SELECT weather, AVG(precipitation) FROM seattle_weather GROUP BY weather;
  Reason: The user requested individual days satisfying a numeric threshold, not group averages.

- Example 4 (Top-N / Extreme):
  User Question: "What was the hottest day?"
  CORRECT:
    SELECT date, temp_max, weather FROM seattle_weather ORDER BY temp_max DESC LIMIT 1;
  INCORRECT:
    SELECT MAX(temp_max) FROM seattle_weather;
  Reason: The user asked for the day (record), which requires ORDER BY and LIMIT 1 so date is visible.

- Example 5 (Dataset Aggregation):
  User Question: "What is the average maximum temperature?"
  CORRECT:
    SELECT ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather;
  INCORRECT:
    SELECT weather, AVG(temp_max) FROM seattle_weather GROUP BY weather;
  Reason: The user asked for the overall average, not an average broken down by weather condition.

- Example 6 (Grouped Breakdown):
  User Question: "What was the average temperature for each weather condition?"
  CORRECT:
    SELECT weather, ROUND(AVG(temp_max), 2) AS avg_temp_max, ROUND(AVG(temp_min), 2) AS avg_temp_min FROM seattle_weather GROUP BY weather;
  Reason: 'For each weather condition' explicitly requests GROUP BY weather.

- Example 7 (Comparative Aggregation):
  User Question: "Which weather condition had the highest average maximum temperature?"
  CORRECT:
    SELECT weather, ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather GROUP BY weather ORDER BY avg_temp_max DESC LIMIT 1;
  INCORRECT:
    SELECT ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather;
  Reason: Answering with only the overall average loses the grouping dimension (weather), the comparison ranking (ORDER BY DESC), and the single winning condition (LIMIT 1).

- Example 8 (Comparative Aggregation with Time Dimension):
  User Question: "Which month had the highest average maximum temperature?"
  CORRECT:
    SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather GROUP BY month ORDER BY avg_temp_max DESC LIMIT 1;
  INCORRECT:
    SELECT date, temp_max FROM seattle_weather ORDER BY temp_max DESC LIMIT 1;
- Example 9 (Composite Constraints: Top-N with Date Range):
  User Question: "Show the 5 days with the highest precipitation during 2012."
  CORRECT:
    SELECT date, precipitation, weather FROM seattle_weather WHERE date >= '2012-01-01' AND date < '2013-01-01' ORDER BY precipitation DESC LIMIT 5;
  INCORRECT:
    SELECT date, precipitation, weather FROM seattle_weather ORDER BY precipitation DESC LIMIT 5;
  Reason: Dropping "during 2012" returns records from other years, completely violating explicit temporal constraints.

- Example 10 (Composite Constraints: Filter + Aggregation + Date Filter):
  User Question: "What was the average maximum temperature during rainy days in 2012?"
  CORRECT:
    SELECT ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather WHERE weather = 'rain' AND date >= '2012-01-01' AND date < '2013-01-01';
  INCORRECT:
    SELECT ROUND(AVG(temp_max), 2) AS avg_temp_max FROM seattle_weather WHERE weather = 'rain';
  Reason: Omitting the date filter computes the average across all years instead of 2012.
"""


class PromptBuilder:
    """Formats database schemas and user natural language questions into optimal LLM/Text2SQL prompts."""

    @staticmethod
    def build_schema_prompt(
        schema_json_str: str,
        user_question: str,
        feedback_issues: Optional[List[str]] = None,
        detected_intent: Optional[str] = None,
    ) -> str:
        """
        Creates a structured prompt mapping schema table definitions, foreign keys, intent rules,
        few-shot examples, and optional previous error feedback for retries.
        """
        try:
            schema_data = json.loads(schema_json_str) if isinstance(schema_json_str, str) else schema_json_str
        except Exception:
            schema_data = {"tables": []}

        table_summaries: List[str] = []
        for table in schema_data.get("tables", []):
            tbl_name = table.get("name", "")
            cols = []
            for col in table.get("columns", []):
                col_str = f"{col.get('name')} ({col.get('type')})"
                if col.get("primary_key"):
                    col_str += " [PK]"
                if col.get("foreign_key"):
                    col_str += f" [FK -> {col.get('foreign_key')}]"
                cols.append(col_str)
            table_summaries.append(f"Table {tbl_name}: {', '.join(cols)}")

        schema_context = "\n".join(table_summaries)

        feedback_section = ""
        if feedback_issues:
            feedback_section = f"""
### CORRECTION REQUIRED FROM PREVIOUS ATTEMPT:
The previous query had the following semantic/validation errors:
{chr(10).join(f"- {iss}" for iss in feedback_issues)}
Please regenerate a corrected SQL query addressing these exact issues.
"""

        intent_section = f"\nDetected Query Intent: {detected_intent}\n" if detected_intent else ""

        prompt = f"""You are a professional Enterprise Text-to-SQL compiler.
Generate clean, highly accurate, read-only SQL queries matching the user's intent.

### DATABASE SCHEMA:
{schema_context}
{intent_section}
{FEW_SHOT_GUIDANCE}
{feedback_section}
### USER QUESTION:
{user_question}

### SQL QUERY (Single executable SELECT statement only, no commentary):
"""
        return prompt

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token count estimator (approx ~4 characters per token)."""
        return max(1, len(text) // 4)


prompt_builder = PromptBuilder()
