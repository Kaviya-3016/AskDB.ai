import time
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.ml.validator import validator


class QueryExecutionService:
    """Safely executes validated read-only SQL queries on the sandboxed target database."""

    @staticmethod
    async def execute_safe_query(
        session: AsyncSession,
        sql_query: str,
        max_rows: int = 500
    ) -> Tuple[bool, List[str], List[Dict[str, Any]], int, float, str]:
        """
        Executes a validated read-only SQL query.
        Returns: (success, columns, rows, row_count, execution_time_ms, error_message)
        """
        # 1. Security check before execution
        is_valid, is_read_only, safety_score, issues, _ = validator.validate_and_sanitize(sql_query)
        if not is_valid:
            error_msg = f"Execution blocked: {'; '.join(issues)}"
            return False, [], [], 0, 0.0, error_msg

        start_time = time.time()
        try:
            # Enforce max rows limit if not already limited
            exec_sql = sql_query.strip().rstrip(";")
            
            result = await session.execute(text(exec_sql))
            columns = list(result.keys()) if result.keys() else []
            raw_rows = result.fetchmany(max_rows)

            rows: List[Dict[str, Any]] = []
            for row in raw_rows:
                row_dict = {}
                for idx, col in enumerate(columns):
                    val = row[idx]
                    # Format float values nicely
                    if isinstance(val, float):
                        val = round(val, 2)
                    elif hasattr(val, "isoformat"):
                        val = val.isoformat()
                    row_dict[col] = val
                rows.append(row_dict)

            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return True, columns, rows, len(rows), execution_time_ms, ""

        except Exception as e:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return False, [], [], 0, execution_time_ms, str(e)


execution_service = QueryExecutionService()
