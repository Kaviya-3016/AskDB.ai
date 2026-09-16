import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import QueryResult, QueryLog
from app.schemas.result import QueryResultDetailResponse, ResultExportRequest
from app.services.export_service import export_service

router = APIRouter(prefix="/results", tags=["Query Results & Export"])


@router.get("/{query_id}", response_model=QueryResultDetailResponse)
async def get_query_results_by_id(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full execution result dataset for a specific query."""
    stmt = (
        select(QueryResult, QueryLog.natural_language_query, QueryLog.executed_sql)
        .join(QueryLog, QueryResult.query_id == QueryLog.id)
        .where(QueryResult.query_id == query_id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query results not found.")

    qr, nl_query, exec_sql = row
    try:
        columns = json.loads(qr.columns_json)
        rows = json.loads(qr.rows_json)
    except Exception:
        columns, rows = [], []

    return QueryResultDetailResponse(
        id=qr.id,
        query_id=qr.query_id,
        natural_language_query=nl_query,
        sql_query=exec_sql,
        columns=columns,
        rows=rows,
        row_count=qr.row_count,
        execution_time_ms=qr.execution_time_ms,
        created_at=qr.created_at,
    )


@router.post("/{query_id}/export")
async def export_query_results(
    query_id: int,
    export_req: ResultExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Export query results as CSV, Excel (.xlsx), or JSON file."""
    stmt = select(QueryResult).where(QueryResult.query_id == query_id)
    res = await db.execute(stmt)
    qr = res.scalars().first()
    if not qr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query results not found.")

    try:
        columns = json.loads(qr.columns_json)
        rows = json.loads(qr.rows_json)
    except Exception:
        columns, rows = [], []

    file_bytes, media_type, ext = export_service.export_data(
        columns=columns,
        rows=rows,
        export_format=export_req.format,
    )

    base_name = export_req.filename or f"query_{query_id}_export"
    filename = f"{base_name}.{ext}"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
