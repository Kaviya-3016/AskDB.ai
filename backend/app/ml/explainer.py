import re
from typing import Dict, Any, List
from app.schemas.query import QueryExplainResponse


class SQLExplainer:
    """Translates SQL syntax and query AST into plain-English logical explanation steps."""

    @staticmethod
    def explain_query(sql_query: str, natural_language_query: str = "") -> QueryExplainResponse:
        clean = sql_query.strip()
        operations: List[str] = []
        tables_involved: List[str] = []
        filter_conditions: List[str] = []
        aggregations: List[str] = []

        # Find tables
        from_tbls = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)", clean, re.IGNORECASE)
        join_tbls = re.findall(r"\bJOIN\s+([a-zA-Z0-9_]+)", clean, re.IGNORECASE)
        tables_involved = list(dict.fromkeys(from_tbls + join_tbls))

        # Find WHERE filters
        where_match = re.search(r"\bWHERE\s+(.*?)(?=\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
        if where_match:
            raw_filters = where_match.group(1).strip()
            filter_conditions = [f.strip() for f in re.split(r"\bAND\b|\bOR\b", raw_filters, flags=re.IGNORECASE) if f.strip()]

        # Find Aggregations
        agg_matches = re.findall(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\((.*?)\)", clean, re.IGNORECASE)
        for fn, col in agg_matches:
            aggregations.append(f"{fn.upper()} calculated on column '{col.strip()}'")

        # Operations breakdown
        if tables_involved:
            operations.append(f"Scans base table '{tables_involved[0]}'")
            for jt in tables_involved[1:]:
                operations.append(f"Performs relational JOIN with table '{jt}'")

        if filter_conditions:
            operations.append(f"Filters records where {', '.join(filter_conditions)}")

        if "GROUP BY" in clean.upper():
            gb_match = re.search(r"\bGROUP BY\s+(.*?)(?=\bORDER BY\b|\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
            if gb_match:
                operations.append(f"Aggregates and groups data by {gb_match.group(1).strip()}")

        if aggregations:
            operations.append(f"Calculates summary metrics: {', '.join(aggregations)}")

        if "ORDER BY" in clean.upper():
            ob_match = re.search(r"\bORDER BY\s+(.*?)(?=\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
            if ob_match:
                operations.append(f"Sorts resulting rows by {ob_match.group(1).strip()}")

        if "LIMIT" in clean.upper():
            lim_match = re.search(r"\bLIMIT\s+(\d+)", clean, re.IGNORECASE)
            if lim_match:
                operations.append(f"Restricts results to the top {lim_match.group(1)} records")

        summary = f"This query retrieves and analyzes records across {', '.join(tables_involved) if tables_involved else 'the database'}."
        if aggregations:
            summary += f" It computes aggregate analytics including {', '.join(aggregations[:2])}."

        return QueryExplainResponse(
            summary=summary,
            operations=operations,
            tables_involved=tables_involved,
            filter_conditions=filter_conditions,
            aggregations=aggregations,
        )


explainer = SQLExplainer()
