from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class QueryResultDetailResponse(BaseModel):
    id: int
    query_id: int
    natural_language_query: Optional[str] = None
    sql_query: Optional[str] = None
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    created_at: datetime


class ResultExportRequest(BaseModel):
    format: str = "csv"  # csv, xlsx, json
    filename: Optional[str] = None
