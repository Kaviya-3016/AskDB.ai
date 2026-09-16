from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SystemAnalyticsResponse(BaseModel):
    total_users: int
    total_queries: int
    successful_queries: int
    failed_queries: int
    blocked_queries: int
    avg_inference_time_ms: float
    avg_execution_time_ms: float
    cache_hit_rate: float
    recent_query_volume: List[Dict[str, Any]]
    top_queried_tables: List[Dict[str, Any]]


class ModelInfoResponse(BaseModel):
    model_name: str
    architecture: str
    status: str
    version: str
    average_latency_ms: float
    average_confidence: float
    cache_ttl_seconds: int
    total_inferences: int
    fallback_engine: str


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource: str
    ip_address: Optional[str] = None
    status: str
    details: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
