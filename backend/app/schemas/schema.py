from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ColumnDefinition(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True
    description: Optional[str] = None


class TableDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[ColumnDefinition] = []


class SchemaUploadRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    dialect: str = "postgres"
    ddl_content: str = Field(..., min_length=10, description="SQL DDL statements (CREATE TABLE ...)")


class SchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    dialect: str
    ddl_content: str
    schema_json: str
    is_default: bool
    created_at: datetime


class TablePreviewResponse(BaseModel):
    table_name: str
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    total_row_count: int


class DatasetUploadResponse(BaseModel):
    schema_id: int
    schema_name: str
    table_name: str
    row_count: int
    columns: List[Dict[str, Any]]
    sample_rows: List[Dict[str, Any]]
    suggested_prompts: List[str]
