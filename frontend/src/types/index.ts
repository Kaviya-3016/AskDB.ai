export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'viewer';
  avatar_url?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface GoogleAuthPayload {
  credential?: string;
  email?: string;
  name?: string;
  picture?: string;
  role?: string;
}

export interface GoogleConfigResponse {
  client_id: string;
  enabled: boolean;
}

export interface ColumnInfo {
  name: string;
  type: string;
  primary_key?: boolean;
  foreign_key?: string | null;
  nullable?: boolean;
  description?: string;
}

export interface TableInfo {
  name: string;
  description?: string;
  columns: ColumnInfo[];
}

export interface SchemaMetadata {
  id: number;
  name: string;
  description?: string;
  dialect: string;
  ddl_content: string;
  schema_json: string;
  is_default: boolean;
  created_at: string;
}

export interface DatasetUploadResponse {
  schema_id: number;
  schema_name: string;
  table_name: string;
  row_count: number;
  columns: ColumnInfo[];
  sample_rows: Record<string, any>[];
  suggested_prompts: string[];
}

export interface QueryGenerateResponse {
  query_id?: number;
  natural_language_query: string;
  generated_sql: string;
  confidence_score: number;
  explanation?: string;
  is_cached: boolean;
  inference_time_ms: number;
  suggested_charts: string[];
}

export interface QueryExecuteResponse {
  query_id: number;
  sql_query: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  status: 'SUCCESS' | 'FAILED' | 'BLOCKED';
  error_message?: string | null;
}

export interface QueryValidateResponse {
  is_valid: boolean;
  is_read_only: boolean;
  safety_score: number;
  issues: string[];
  formatted_sql?: string;
  ast_summary?: {
    tables: string[];
    statement_type: string;
    has_where: boolean;
    has_group_by: boolean;
    has_order_by: boolean;
    has_limit: boolean;
  };
}

export interface QueryExplainResponse {
  summary: string;
  operations: string[];
  tables_involved: string[];
  filter_conditions: string[];
  aggregations: string[];
}

export interface SavedQuery {
  id: number;
  user_id: number;
  query_id?: number;
  title: string;
  natural_language_query: string;
  sql_query: string;
  tags: string[];
  is_favorite: boolean;
  created_at: string;
}

export interface QueryHistoryItem {
  id: number;
  schema_id: number;
  schema_name?: string;
  natural_language_query: string;
  generated_sql: string;
  executed_sql?: string;
  confidence_score: number;
  status: 'GENERATED' | 'SUCCESS' | 'FAILED' | 'BLOCKED';
  execution_time_ms: number;
  is_cached: boolean;
  is_favorite?: boolean;
  created_at: string;
}

export interface SystemAnalytics {
  total_users: number;
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  blocked_queries: number;
  avg_inference_time_ms: number;
  avg_execution_time_ms: number;
  cache_hit_rate: number;
  recent_query_volume: Array<{ timestamp: string; queries: number; errors: number }>;
  top_queried_tables: Array<{ table_name: string; query_count: number }>;
}

export interface ModelInfo {
  model_name: string;
  architecture: string;
  status: string;
  version: string;
  average_latency_ms: number;
  average_confidence: number;
  cache_ttl_seconds: number;
  total_inferences: number;
  fallback_engine: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  user_email?: string;
  action: string;
  resource: string;
  ip_address?: string;
  status: string;
  details: Record<string, any>;
  created_at: string;
}

export interface TablePreview {
  table_name: string;
  columns: string[];
  sample_rows: Record<string, any>[];
  total_row_count: number;
}

export interface StreamTokenChunk {
  type: 'status' | 'token' | 'complete' | 'query_id' | 'error';
  status?: string;
  message?: string;
  token?: string;
  query_id?: number;
  error?: string;
  natural_language_query?: string;
  generated_sql?: string;
  confidence_score?: number;
  explanation?: string;
  inference_time_ms?: number;
  suggested_charts?: string[];
  model_name?: string;
  is_cached?: boolean;
  is_valid?: boolean;
  is_read_only?: boolean;
}
