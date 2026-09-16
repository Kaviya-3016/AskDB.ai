import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from app.core.database import get_db, get_demo_db
from app.db.models import QueryLog, QueryResult, SavedQuery, SchemaMetadata, User, ModelMetric
from app.schemas.query import (
    QueryGenerateRequest,
    QueryGenerateResponse,
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryValidateRequest,
    QueryValidateResponse,
    QueryExplainRequest,
    QueryExplainResponse,
    SaveQueryRequest,
    SavedQueryResponse,
    QueryHistoryResponse,
)
from app.api.deps import get_current_user_optional, get_current_user, apply_rate_limiting
from app.ml.model_service import model_service
from app.ml.validator import validator
from app.ml.explainer import explainer
from app.services.execution_service import execution_service
from app.services.query_service import query_service

router = APIRouter(prefix="/queries", tags=["Queries & Inference"])


@router.post("/generate/stream", dependencies=[Depends(apply_rate_limiting)])
async def generate_sql_query_stream(
    req_body: QueryGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint for Text-to-SQL generation.
    Streams tokens as they are inferred, validates with AST safety firewall, and returns final payload.
    """
    stmt = select(SchemaMetadata).where(SchemaMetadata.id == req_body.schema_id)
    res = await db.execute(stmt)
    schema_obj = res.scalars().first()
    if not schema_obj:
        # Fallback to default or first available schema
        stmt_fb = select(SchemaMetadata).order_by(SchemaMetadata.is_default.desc(), SchemaMetadata.id.asc())
        res_fb = await db.execute(stmt_fb)
        schema_obj = res_fb.scalars().first()

    if not schema_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target schema not found.")

    async def event_generator():
        try:
            complete_result = None
            async for chunk in model_service.generate_sql_stream(
                schema_id=schema_obj.id,
                schema_json_str=schema_obj.schema_json,
                user_prompt=req_body.prompt,
                temperature=req_body.temperature or 0.1,
                model_name=req_body.model_name or "querycraft-ultra",
            ):
                if chunk.get("type") == "complete":
                    complete_result = chunk
                yield f"data: {json.dumps(chunk)}\n\n"

            # Record in query logs if complete
            if complete_result:
                user_id = current_user.id if current_user else None
                q_log = await query_service.create_query_log(
                    session=db,
                    user_id=user_id,
                    schema_id=schema_obj.id,
                    natural_language_query=req_body.prompt,
                    generated_sql=complete_result["generated_sql"],
                    confidence_score=complete_result["confidence_score"],
                    is_cached=complete_result.get("is_cached", False),
                )
                # Emit the assigned query_id event
                yield f"data: {json.dumps({'type': 'query_id', 'query_id': q_log.id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



@router.post("/generate", response_model=QueryGenerateResponse, dependencies=[Depends(apply_rate_limiting)])
async def generate_sql_query(
    req_body: QueryGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Generate SQL from natural language prompt given a target schema."""
    # 1. Fetch schema definition
    stmt = select(SchemaMetadata).where(SchemaMetadata.id == req_body.schema_id)
    res = await db.execute(stmt)
    schema_obj = res.scalars().first()
    if not schema_obj:
        stmt_fb = select(SchemaMetadata).order_by(SchemaMetadata.is_default.desc(), SchemaMetadata.id.asc())
        res_fb = await db.execute(stmt_fb)
        schema_obj = res_fb.scalars().first()

    if not schema_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target schema not found.")

    # 2. Run inference pipeline
    inference_result = await model_service.generate_sql(
        schema_id=schema_obj.id,
        schema_json_str=schema_obj.schema_json,
        user_prompt=req_body.prompt,
        temperature=req_body.temperature or 0.1,
    )

    # 3. Log query generation in DB
    user_id = current_user.id if current_user else None
    q_log = await query_service.create_query_log(
        session=db,
        user_id=user_id,
        schema_id=schema_obj.id,
        natural_language_query=req_body.prompt,
        generated_sql=inference_result["generated_sql"],
        confidence_score=inference_result["confidence_score"],
        is_cached=inference_result["is_cached"],
    )

    # Record model performance metric
    metric = ModelMetric(
        model_name=model_service.model_name,
        inference_time_ms=inference_result["inference_time_ms"],
        prompt_tokens=inference_result.get("prompt_tokens", 0),
        completion_tokens=inference_result.get("completion_tokens", 0),
        confidence_score=inference_result["confidence_score"],
    )
    db.add(metric)

    return QueryGenerateResponse(
        query_id=q_log.id,
        natural_language_query=req_body.prompt,
        generated_sql=inference_result["generated_sql"],
        confidence_score=inference_result["confidence_score"],
        explanation=inference_result["explanation"],
        is_cached=inference_result["is_cached"],
        inference_time_ms=inference_result["inference_time_ms"],
        suggested_charts=inference_result["suggested_charts"],
    )


@router.post("/execute", response_model=QueryExecuteResponse, dependencies=[Depends(apply_rate_limiting)])
async def execute_query(
    req_body: QueryExecuteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    demo_db: AsyncSession = Depends(get_demo_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Safely execute a generated or user-edited SQL query against the sandboxed target database."""
    user_id = current_user.id if current_user else None
    user_email = current_user.email if current_user else "anonymous"

    # 1. Execute query in safe sandboxed session
    success, columns, rows, row_count, execution_time_ms, err_msg = (
        await execution_service.execute_safe_query(
            session=demo_db,
            sql_query=req_body.sql_query,
            max_rows=req_body.max_rows or 500,
        )
    )

    query_status = "SUCCESS" if success else "FAILED"
    client_ip = request.client.host if request.client else None

    # 2. Persist log & result
    query_id = req_body.query_id
    if not query_id:
        target_schema_id = req_body.schema_id
        if target_schema_id:
            chk = await db.execute(select(SchemaMetadata.id).where(SchemaMetadata.id == target_schema_id))
            if not chk.scalar():
                target_schema_id = None
        if not target_schema_id:
            fb = await db.execute(select(SchemaMetadata.id).order_by(SchemaMetadata.is_default.desc(), SchemaMetadata.id.asc()))
            target_schema_id = fb.scalar() or 1

        q_log = await query_service.create_query_log(
            session=db,
            user_id=user_id,
            schema_id=target_schema_id,
            natural_language_query=req_body.natural_language_query or "Direct SQL Execution",
            generated_sql=req_body.sql_query,
            confidence_score=1.0,
            is_cached=False,
        )
        query_id = q_log.id

    await query_service.save_execution_result(
        session=db,
        query_id=query_id,
        executed_sql=req_body.sql_query,
        columns=columns,
        rows=rows,
        row_count=row_count,
        execution_time_ms=execution_time_ms,
        status=query_status,
        error_message=err_msg if not success else None,
    )

    # 3. Audit trail
    await query_service.log_audit_event(
        db,
        user_id,
        user_email,
        "QUERY_EXECUTE",
        f"query:{query_id}",
        client_ip,
        query_status,
        {"row_count": row_count, "execution_time_ms": execution_time_ms},
    )

    return QueryExecuteResponse(
        query_id=query_id,
        sql_query=req_body.sql_query,
        columns=columns,
        rows=rows,
        row_count=row_count,
        execution_time_ms=execution_time_ms,
        status=query_status,
        error_message=err_msg if not success else None,
    )


@router.post("/validate", response_model=QueryValidateResponse)
async def validate_query(req_body: QueryValidateRequest):
    """Validate a SQL statement for injection risks, destructive operations, and syntax correctness."""
    is_valid, is_read_only, safety_score, issues, formatted_sql = validator.validate_and_sanitize(req_body.sql_query)
    ast_summary = validator.extract_ast_summary(req_body.sql_query) if is_valid else None

    return QueryValidateResponse(
        is_valid=is_valid,
        is_read_only=is_read_only,
        safety_score=safety_score,
        issues=issues,
        formatted_sql=formatted_sql,
        ast_summary=ast_summary,
    )


@router.post("/explain", response_model=QueryExplainResponse)
async def explain_query(req_body: QueryExplainRequest):
    """Break down the logical execution and operations of a SQL query in plain English."""
    return explainer.explain_query(req_body.sql_query, req_body.natural_language_query or "")


@router.get("/history", response_model=List[QueryHistoryResponse])
async def get_query_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Fetch user or global query history log."""
    user_id = current_user.id if current_user else None
    history_records = await query_service.get_user_history(db, user_id=user_id, limit=limit)
    return [QueryHistoryResponse(**r) for r in history_records]


@router.post("/save", response_model=SavedQueryResponse, status_code=status.HTTP_201_CREATED)
async def save_query_bookmark(
    req_body: SaveQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark and save a natural language / SQL query for quick access."""
    saved = SavedQuery(
        user_id=current_user.id,
        query_id=req_body.query_id,
        title=req_body.title,
        natural_language_query=req_body.natural_language_query,
        sql_query=req_body.sql_query,
        tags=json.dumps(req_body.tags),
        is_favorite=req_body.is_favorite,
    )
    db.add(saved)
    await db.flush()

    return SavedQueryResponse(
        id=saved.id,
        user_id=saved.user_id,
        query_id=saved.query_id,
        title=saved.title,
        natural_language_query=saved.natural_language_query,
        sql_query=saved.sql_query,
        tags=req_body.tags,
        is_favorite=saved.is_favorite,
        created_at=saved.created_at,
    )


@router.get("/saved", response_model=List[SavedQueryResponse])
async def list_saved_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all saved queries bookmarked by the current user."""
    stmt = (
        select(SavedQuery)
        .where(SavedQuery.user_id == current_user.id)
        .order_by(desc(SavedQuery.is_favorite), desc(SavedQuery.created_at))
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    results = []
    for r in records:
        try:
            tags_list = json.loads(r.tags)
        except Exception:
            tags_list = []
        results.append(
            SavedQueryResponse(
                id=r.id,
                user_id=r.user_id,
                query_id=r.query_id,
                title=r.title,
                natural_language_query=r.natural_language_query,
                sql_query=r.sql_query,
                tags=tags_list,
                is_favorite=r.is_favorite,
                created_at=r.created_at,
            )
        )
    return results


@router.delete("/{query_id}", status_code=status.HTTP_200_OK)
async def delete_query_log(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a query log from history."""
    stmt = select(QueryLog).where(QueryLog.id == query_id)
    res = await db.execute(stmt)
    q_log = res.scalars().first()
    if not q_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query log not found.")

    if current_user.role != "admin" and q_log.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this query log.")

    await db.delete(q_log)
    return {"message": f"Query log #{query_id} deleted successfully."}
