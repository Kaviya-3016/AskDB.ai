import axios from 'axios';
import {
  User,
  AuthTokens,
  GoogleAuthPayload,
  GoogleConfigResponse,
  SchemaMetadata,
  DatasetUploadResponse,
  QueryGenerateResponse,
  QueryExecuteResponse,
  QueryValidateResponse,
  QueryExplainResponse,
  SavedQuery,
  QueryHistoryItem,
  SystemAnalytics,
  ModelInfo,
  AuditLog,
  TablePreview,
  StreamTokenChunk,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Bearer token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = res.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  }
);

// API Service Functions
export const api = {
  // Auth
  login: async (email: string, password: string): Promise<AuthTokens> => {
    const res = await apiClient.post<AuthTokens>('/auth/login', { email, password });
    return res.data;
  },
  register: async (email: string, password: string, full_name: string, role: string): Promise<AuthTokens> => {
    const res = await apiClient.post<AuthTokens>('/auth/register', { email, password, full_name, role });
    return res.data;
  },
  googleAuth: async (payload: GoogleAuthPayload): Promise<AuthTokens> => {
    const res = await apiClient.post<AuthTokens>('/auth/google', payload);
    return res.data;
  },
  getGoogleConfig: async (): Promise<GoogleConfigResponse> => {
    const res = await apiClient.get<GoogleConfigResponse>('/auth/google/config');
    return res.data;
  },
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },
  getCurrentUser: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  // Schemas
  getSchemas: async (): Promise<SchemaMetadata[]> => {
    const res = await apiClient.get<SchemaMetadata[]>('/schemas');
    return res.data;
  },
  getSchemaById: async (id: number): Promise<SchemaMetadata> => {
    const res = await apiClient.get<SchemaMetadata>(`/schemas/${id}`);
    return res.data;
  },
  uploadSchema: async (data: { name: string; description?: string; dialect: string; ddl_content: string }): Promise<SchemaMetadata> => {
    const res = await apiClient.post<SchemaMetadata>('/schemas/upload', data);
    return res.data;
  },
  uploadDataset: async (file: File, datasetName?: string, tableName?: string): Promise<DatasetUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) formData.append('dataset_name', datasetName);
    if (tableName) formData.append('table_name', tableName);

    const res = await apiClient.post<DatasetUploadResponse>('/schemas/upload-dataset', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  getSchemaTables: async (schemaId: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>(`/schemas/${schemaId}/tables`);
    return res.data;
  },
  previewTable: async (schemaId: number, tableName: string, limit = 10): Promise<TablePreview> => {
    const res = await apiClient.get<TablePreview>(`/schemas/${schemaId}/preview`, {
      params: { table_name: tableName, limit },
    });
    return res.data;
  },

  // Queries
  generateSQL: async (schemaId: number, prompt: string): Promise<QueryGenerateResponse> => {
    const res = await apiClient.post<QueryGenerateResponse>('/queries/generate', {
      schema_id: schemaId,
      prompt,
    });
    return res.data;
  },
  generateSQLStream: async (
    schemaId: number,
    prompt: string,
    modelName: string = 'querycraft-ultra',
    onChunk?: (chunk: StreamTokenChunk) => void
  ): Promise<QueryGenerateResponse> => {
    const token = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/queries/generate/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        schema_id: schemaId,
        prompt,
        model_name: modelName,
      }),
    });

    if (!response.ok) {
      let errorMsg = 'Failed to generate SQL stream.';
      try {
        const errJson = await response.json();
        errorMsg = errJson.detail || errorMsg;
      } catch (e) {}
      throw new Error(errorMsg);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('ReadableStream not supported on this browser.');
    }

    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let completeResponse: QueryGenerateResponse | null = null;
    let assignedQueryId: number | undefined = undefined;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          const jsonStr = trimmed.slice(5).trim();
          if (jsonStr) {
            try {
              const chunk: StreamTokenChunk = JSON.parse(jsonStr);
              if (onChunk) onChunk(chunk);
              if (chunk.type === 'query_id' && chunk.query_id) {
                assignedQueryId = chunk.query_id;
              }
              if (chunk.type === 'complete') {
                completeResponse = {
                  query_id: assignedQueryId || chunk.query_id,
                  natural_language_query: chunk.natural_language_query || prompt,
                  generated_sql: chunk.generated_sql || '',
                  confidence_score: chunk.confidence_score || 0.95,
                  explanation: chunk.explanation,
                  is_cached: chunk.is_cached || false,
                  inference_time_ms: chunk.inference_time_ms || 100,
                  suggested_charts: chunk.suggested_charts || ['table'],
                };
              }
            } catch (err) {
              console.warn('Failed to parse SSE chunk:', jsonStr, err);
            }
          }
        }
      }
    }

    if (completeResponse && assignedQueryId) {
      completeResponse.query_id = assignedQueryId;
    }

    if (!completeResponse) {
      throw new Error('Stream completed without valid response.');
    }

    return completeResponse;
  },
  executeSQL: async (schemaId: number, sqlQuery: string, queryId?: number, naturalLanguageQuery?: string): Promise<QueryExecuteResponse> => {
    const res = await apiClient.post<QueryExecuteResponse>('/queries/execute', {
      schema_id: schemaId,
      sql_query: sqlQuery,
      query_id: queryId,
      natural_language_query: naturalLanguageQuery,
    });
    return res.data;
  },
  validateSQL: async (sqlQuery: string): Promise<QueryValidateResponse> => {
    const res = await apiClient.post<QueryValidateResponse>('/queries/validate', {
      sql_query: sqlQuery,
    });
    return res.data;
  },
  explainSQL: async (sqlQuery: string, naturalLanguageQuery?: string): Promise<QueryExplainResponse> => {
    const res = await apiClient.post<QueryExplainResponse>('/queries/explain', {
      sql_query: sqlQuery,
      natural_language_query: naturalLanguageQuery,
    });
    return res.data;
  },
  getHistory: async (limit = 50): Promise<QueryHistoryItem[]> => {
    const res = await apiClient.get<QueryHistoryItem[]>('/queries/history', {
      params: { limit },
    });
    return res.data;
  },
  saveQuery: async (data: { title: string; natural_language_query: string; sql_query: string; tags: string[]; query_id?: number }): Promise<SavedQuery> => {
    const res = await apiClient.post<SavedQuery>('/queries/save', data);
    return res.data;
  },
  getSavedQueries: async (): Promise<SavedQuery[]> => {
    const res = await apiClient.get<SavedQuery[]>('/queries/saved');
    return res.data;
  },
  deleteQuery: async (queryId: number): Promise<void> => {
    await apiClient.delete(`/queries/${queryId}`);
  },

  // Export
  exportResults: async (queryId: number, format: 'csv' | 'xlsx' | 'json', filename?: string): Promise<Blob> => {
    const res = await apiClient.post(
      `/results/${queryId}/export`,
      { format, filename },
      { responseType: 'blob' }
    );
    return res.data;
  },

  // Admin
  getAdminUsers: async (): Promise<User[]> => {
    const res = await apiClient.get<User[]>('/admin/users');
    return res.data;
  },
  getAdminAnalytics: async (): Promise<SystemAnalytics> => {
    const res = await apiClient.get<SystemAnalytics>('/admin/analytics');
    return res.data;
  },
  getAdminModels: async (): Promise<ModelInfo> => {
    const res = await apiClient.get<ModelInfo>('/admin/models');
    return res.data;
  },
  getAdminAuditLogs: async (limit = 50): Promise<AuditLog[]> => {
    const res = await apiClient.get<AuditLog[]>('/admin/audit-logs', { params: { limit } });
    return res.data;
  },
};
