from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryGenerateRequest(BaseModel):
    schema_id: int
    prompt: str = Field(..., min_length=3, max_length=1000, description="Natural language question or request")
    temperature: Optional[float] = 0.1
    model_name: Optional[str] = Field("querycraft-ultra", description="Target model engine (querycraft-ultra, gemini-flash, deepseek-sql)")


class QueryGenerateResponse(BaseModel):
    query_id: Optional[int] = None
    natural_language_query: str
    generated_sql: str
    confidence_score: float
    explanation: Optional[str] = None
    is_cached: bool = False
    inference_time_ms: float
    suggested_charts: List[str] = []


class QueryExecuteRequest(BaseModel):
    schema_id: int
    sql_query: str = Field(..., min_length=6, description="SQL query to execute against sandboxed target database")
    query_id: Optional[int] = None
    natural_language_query: Optional[str] = None
    max_rows: Optional[int] = 500


class QueryExecuteResponse(BaseModel):
    query_id: int
    sql_query: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    status: str
    error_message: Optional[str] = None


class QueryValidateRequest(BaseModel):
    sql_query: str


class QueryValidateResponse(BaseModel):
    is_valid: bool
    is_read_only: bool
    safety_score: float
    issues: List[str] = []
    formatted_sql: Optional[str] = None
    ast_summary: Optional[Dict[str, Any]] = None


class QueryExplainRequest(BaseModel):
    sql_query: str
    natural_language_query: Optional[str] = None


class QueryExplainResponse(BaseModel):
    summary: str
    operations: List[str]
    tables_involved: List[str]
    filter_conditions: List[str]
    aggregations: List[str]


class SaveQueryRequest(BaseModel):
    query_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=200)
    natural_language_query: str
    sql_query: str
    tags: List[str] = []
    is_favorite: bool = False


class SavedQueryResponse(BaseModel):
    id: int
    user_id: int
    query_id: Optional[int] = None
    title: str
    natural_language_query: str
    sql_query: str
    tags: List[str] = []
    is_favorite: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    id: int
    schema_id: int
    schema_name: Optional[str] = None
    natural_language_query: str
    generated_sql: str
    executed_sql: Optional[str] = None
    confidence_score: float
    status: str
    execution_time_ms: float
    is_cached: bool
    is_favorite: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
