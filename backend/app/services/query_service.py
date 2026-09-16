import json
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, delete
from app.db.models import QueryLog, QueryResult, SavedQuery, AuditLog, SchemaMetadata, User


class QueryService:
    """Manages query persistence, history queries, saved queries, and audit trails."""

    @staticmethod
    async def create_query_log(
        session: AsyncSession,
        user_id: Optional[int],
        schema_id: int,
        natural_language_query: str,
        generated_sql: str,
        confidence_score: float,
        is_cached: bool = False,
    ) -> QueryLog:
        query_log = QueryLog(
            user_id=user_id,
            schema_id=schema_id,
            natural_language_query=natural_language_query,
            generated_sql=generated_sql,
            confidence_score=confidence_score,
            status="GENERATED",
            is_cached=is_cached,
        )
        session.add(query_log)
        await session.flush()
        return query_log

    @staticmethod
    async def save_execution_result(
        session: AsyncSession,
        query_id: int,
        executed_sql: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        row_count: int,
        execution_time_ms: float,
        status: str,
        error_message: Optional[str] = None,
    ) -> QueryResult:
        # Update QueryLog record
        q_stmt = select(QueryLog).where(QueryLog.id == query_id)
        res = await session.execute(q_stmt)
        q_log = res.scalars().first()
        if q_log:
            q_log.executed_sql = executed_sql
            q_log.status = status
            q_log.execution_time_ms = execution_time_ms
            q_log.error_message = error_message
            session.add(q_log)

        # Store or replace QueryResult
        qr_stmt = select(QueryResult).where(QueryResult.query_id == query_id)
        qr_res = await session.execute(qr_stmt)
        q_result = qr_res.scalars().first()

        if not q_result:
            q_result = QueryResult(
                query_id=query_id,
                columns_json=json.dumps(columns),
                rows_json=json.dumps(rows),
                row_count=row_count,
                execution_time_ms=execution_time_ms,
            )
            session.add(q_result)
        else:
            q_result.columns_json = json.dumps(columns)
            q_result.rows_json = json.dumps(rows)
            q_result.row_count = row_count
            q_result.execution_time_ms = execution_time_ms
            session.add(q_result)

        await session.flush()
        return q_result

    @staticmethod
    async def get_user_history(
        session: AsyncSession,
        user_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(QueryLog, SchemaMetadata.name.label("schema_name"))
            .join(SchemaMetadata, QueryLog.schema_id == SchemaMetadata.id, isouter=True)
            .order_by(desc(QueryLog.created_at))
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(QueryLog.user_id == user_id)

        result = await session.execute(stmt)
        records = []
        for q_log, schema_name in result.all():
            records.append({
                "id": q_log.id,
                "schema_id": q_log.schema_id,
                "schema_name": schema_name or "Custom Schema",
                "natural_language_query": q_log.natural_language_query,
                "generated_sql": q_log.generated_sql,
                "executed_sql": q_log.executed_sql,
                "confidence_score": q_log.confidence_score,
                "status": q_log.status,
                "execution_time_ms": q_log.execution_time_ms,
                "is_cached": q_log.is_cached,
                "created_at": q_log.created_at,
            })
        return records

    @staticmethod
    async def log_audit_event(
        session: AsyncSession,
        user_id: Optional[int],
        user_email: Optional[str],
        action: str,
        resource: str,
        ip_address: Optional[str],
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ):
        audit = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            ip_address=ip_address,
            status=status,
            details_json=json.dumps(details or {}),
        )
        session.add(audit)
        await session.flush()


query_service = QueryService()
