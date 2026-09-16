import io
import json
import re
from typing import List, Dict, Any, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db, get_demo_db
from app.db.models import SchemaMetadata, User
from app.schemas.schema import (
    SchemaResponse,
    SchemaUploadRequest,
    TablePreviewResponse,
    TableDefinition,
    DatasetUploadResponse,
)
from app.api.deps import get_current_user_optional, get_current_user
from app.core.redis import cache_service

router = APIRouter(prefix="/schemas", tags=["Database Schemas"])


def sanitize_identifier(name: str) -> str:
    """Sanitizes table/column name into valid SQL alphanumeric snake_case identifier."""
    clean = re.sub(r"[^\w]+", "_", name.strip().lower()).strip("_")
    if not clean:
        clean = "col"
    if clean[0].isdigit():
        clean = f"c_{clean}"
    return clean[:60]


def infer_sql_type(dtype: str, sample_val: Any) -> str:
    """Infers standard SQL data type from pandas column dtype and values."""
    dt_str = str(dtype).lower()
    if "int" in dt_str:
        return "INTEGER"
    elif "float" in dt_str or "double" in dt_str or "decimal" in dt_str:
        return "NUMERIC(10,2)"
    elif "datetime" in dt_str:
        return "TIMESTAMP"
    elif "bool" in dt_str:
        return "BOOLEAN"
    return "VARCHAR(255)"


def generate_suggested_prompts(table_name: str, columns: List[Dict[str, Any]]) -> List[str]:
    """Generates dynamic natural language questions based on the dataset's columns."""
    prompts = []
    numeric_cols = [c["name"] for c in columns if any(t in c["type"] for t in ["INT", "NUM", "FLOAT", "DECIMAL"])]
    categorical_cols = [c["name"] for c in columns if "VARCHAR" in c["type"] or "TEXT" in c["type"]]

    if categorical_cols and numeric_cols:
        cat = categorical_cols[0]
        num = numeric_cols[0]
        prompts.append(f"Show total {num} by {cat}")
        prompts.append(f"Top 5 {cat} with highest {num}")
        prompts.append(f"What is the average {num} per {cat}?")
    elif numeric_cols:
        num = numeric_cols[0]
        prompts.append(f"Show top 10 records sorted by {num} highest")
        prompts.append(f"What is the average {num} across all records?")
    elif categorical_cols:
        cat = categorical_cols[0]
        prompts.append(f"Count of records grouped by {cat}")

    prompts.append(f"Show the first 25 records from {table_name}")
    return prompts[:4]


def parse_ddl_to_json(ddl: str) -> Dict[str, Any]:
    """Simple parser converting raw DDL into schema JSON format."""
    tables = []
    create_table_blocks = re.findall(
        r"CREATE\s+TABLE\s+([a-zA-Z0-9_]+)\s*\((.*?)\);", ddl, re.IGNORECASE | re.DOTALL
    )
    for tbl_name, body in create_table_blocks:
        columns = []
        for line in body.split(","):
            line = line.strip()
            if not line or line.upper().startswith("CONSTRAINT") or line.upper().startswith("PRIMARY KEY ("):
                continue
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0].strip('"`')
                col_type = parts[1].upper()
                is_pk = "PRIMARY KEY" in line.upper()
                fk_match = re.search(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*\(([a-zA-Z0-9_]+)\)", line, re.IGNORECASE)
                fk = f"{fk_match.group(1)}.{fk_match.group(2)}" if fk_match else None
                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "primary_key": is_pk,
                    "foreign_key": fk,
                    "nullable": "NOT NULL" not in line.upper(),
                })
        tables.append({"name": tbl_name, "description": f"Table storing {tbl_name} data", "columns": columns})

    return {"tables": tables}


@router.get("", response_model=List[SchemaResponse])
async def list_schemas(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve all available database schemas (default system schemas + uploaded custom datasets)."""
    stmt = select(SchemaMetadata).order_by(SchemaMetadata.is_default.desc(), SchemaMetadata.id.asc())
    res = await db.execute(stmt)
    schemas = res.scalars().all()
    return [SchemaResponse.model_validate(s) for s in schemas]


@router.post("/upload", response_model=SchemaResponse, status_code=status.HTTP_201_CREATED)
async def upload_ddl_schema(
    req_body: SchemaUploadRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Upload custom DDL to create a new schema metadata entity."""
    parsed_json = parse_ddl_to_json(req_body.ddl_content)
    if not parsed_json["tables"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse valid CREATE TABLE statements from the provided DDL.",
        )

    user_id = current_user.id if current_user else None
    new_schema = SchemaMetadata(
        user_id=user_id,
        name=req_body.name,
        description=req_body.description,
        dialect=req_body.dialect,
        ddl_content=req_body.ddl_content,
        schema_json=json.dumps(parsed_json),
        is_default=False,
    )
    db.add(new_schema)
    await db.commit()
    await db.refresh(new_schema)

    return SchemaResponse.model_validate(new_schema)


@router.post("/upload-dataset", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_realtime_dataset(
    file: UploadFile = File(..., description="CSV, Excel (.xlsx/.xls), or JSON dataset file"),
    dataset_name: Optional[str] = Form(None),
    table_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    demo_db: AsyncSession = Depends(get_demo_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Upload a real-time dataset file (CSV / Excel / JSON):
    1. Parses file into dataframe & infers schema data types.
    2. Creates a live table in the sandboxed database.
    3. Ingests all rows into the database table.
    4. Registers the schema with dynamic NL prompt suggestions.
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded_dataset.csv"
    ext = filename.split(".")[-1].lower() if "." in filename else "csv"

    # 1. Parse into DataFrame
    try:
        if ext in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif ext == "json":
            df = pd.read_json(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse dataset file '{filename}': {str(e)}",
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded dataset file contains no records.",
        )

    # 2. Clean and sanitize column names
    original_cols = list(df.columns)
    sanitized_cols = [sanitize_identifier(str(col)) for col in original_cols]
    
    # Handle duplicate sanitized names
    seen = {}
    unique_cols = []
    for c in sanitized_cols:
        if c in seen:
            seen[c] += 1
            unique_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 1
            unique_cols.append(c)

    df.columns = unique_cols
    df = df.where(pd.notnull(df), None)

    # 3. Determine table and schema names
    base_name = filename.rsplit(".", 1)[0] if "." in filename else "dataset"
    clean_tbl_name = sanitize_identifier(table_name or base_name)
    schema_title = dataset_name or f"{base_name.replace('_', ' ').title()} Dataset"

    # 4. Build column definitions & CREATE TABLE DDL
    col_defs = []
    ddl_lines = []
    for col_name in unique_cols:
        sample_val = df[col_name].dropna().iloc[0] if not df[col_name].dropna().empty else None
        sql_type = infer_sql_type(df[col_name].dtype, sample_val)
        col_defs.append({
            "name": col_name,
            "type": sql_type,
            "primary_key": False,
            "nullable": True,
        })
        ddl_lines.append(f"    {col_name} {sql_type}")

    ddl_statement = f"CREATE TABLE IF NOT EXISTS {clean_tbl_name} (\n" + ",\n".join(ddl_lines) + "\n);"

    # 5. Execute DDL & Ingest data into sandbox DB
    try:
        await demo_db.execute(text(f"DROP TABLE IF EXISTS {clean_tbl_name};"))
        await demo_db.execute(text(ddl_statement))

        records = df.to_dict(orient="records")
        for chunk_idx in range(0, len(records), 500):
            chunk = records[chunk_idx : chunk_idx + 500]
            col_names_str = ", ".join(unique_cols)
            placeholders = ", ".join([f":{c}" for c in unique_cols])
            insert_sql = f"INSERT INTO {clean_tbl_name} ({col_names_str}) VALUES ({placeholders})"
            await demo_db.execute(text(insert_sql), chunk)

        await demo_db.commit()
    except Exception as e:
        await demo_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create database table or insert records: {str(e)}",
        )

    # 6. Register Schema in Application DB
    schema_json_data = {
        "tables": [
            {
                "name": clean_tbl_name,
                "description": f"Real-time uploaded dataset table for '{filename}'",
                "columns": col_defs,
            }
        ]
    }

    user_id = current_user.id if current_user else None
    new_schema = SchemaMetadata(
        user_id=user_id,
        name=schema_title,
        description=f"Live dataset with {len(df)} records and {len(unique_cols)} attributes from {filename}.",
        dialect="postgres",
        ddl_content=ddl_statement,
        schema_json=json.dumps(schema_json_data),
        is_default=False,
    )
    db.add(new_schema)
    await db.commit()
    await db.refresh(new_schema)

    # 7. Generate suggested prompts & sample rows
    suggested_prompts = generate_suggested_prompts(clean_tbl_name, col_defs)
    sample_preview = records[:10]

    return DatasetUploadResponse(
        schema_id=new_schema.id,
        schema_name=new_schema.name,
        table_name=clean_tbl_name,
        row_count=len(df),
        columns=col_defs,
        sample_rows=sample_preview,
        suggested_prompts=suggested_prompts,
    )


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema_by_id(
    schema_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific schema by ID."""
    stmt = select(SchemaMetadata).where(SchemaMetadata.id == schema_id)
    res = await db.execute(stmt)
    schema_obj = res.scalars().first()
    if not schema_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found.")
    return SchemaResponse.model_validate(schema_obj)


@router.get("/{schema_id}/tables", response_model=List[Dict[str, Any]])
async def get_schema_tables(
    schema_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get tables and column structure list for a specific schema."""
    stmt = select(SchemaMetadata).where(SchemaMetadata.id == schema_id)
    res = await db.execute(stmt)
    schema_obj = res.scalars().first()
    if not schema_obj:
        stmt_fb = select(SchemaMetadata).order_by(SchemaMetadata.is_default.desc(), SchemaMetadata.id.asc())
        res_fb = await db.execute(stmt_fb)
        schema_obj = res_fb.scalars().first()

    if not schema_obj:
        return []

    try:
        data = json.loads(schema_obj.schema_json)
        return data.get("tables", [])
    except Exception:
        return []


@router.get("/{schema_id}/preview", response_model=TablePreviewResponse)
async def preview_table_data(
    schema_id: int,
    table_name: str = Query(..., description="Name of the table to preview"),
    limit: int = Query(10, ge=1, le=50),
    demo_db: AsyncSession = Depends(get_demo_db),
):
    """Preview live sample data rows for any table in the sandboxed target database."""
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid table name format.")

    try:
        count_res = await demo_db.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
        total_count = count_res.scalar() or 0

        rows_res = await demo_db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit};"))
        columns = list(rows_res.keys())
        raw_rows = rows_res.fetchall()

        rows = []
        for r in raw_rows:
            row_dict = {}
            for idx, col in enumerate(columns):
                val = r[idx]
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                row_dict[col] = val
            rows.append(row_dict)

        return TablePreviewResponse(
            table_name=table_name,
            columns=columns,
            sample_rows=rows,
            total_row_count=total_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not preview table '{table_name}': {str(e)}",
        )
