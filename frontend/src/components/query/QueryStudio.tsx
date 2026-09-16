import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Wand2,
  Table as TableIcon,
  BarChart3,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  SchemaMetadata,
  TableInfo,
  QueryGenerateResponse,
  QueryExecuteResponse,
  QueryExplainResponse,
  QueryHistoryItem,
} from '../../types';
import { SQLViewer } from './SQLViewer';
import { QueryExplainer } from './QueryExplainer';
import { ResultsTable } from '../results/ResultsTable';
import { DataVisualizer } from '../results/DataVisualizer';
import { SchemaExplorer } from '../schema/SchemaExplorer';
import { TablePreviewModal } from '../schema/TablePreviewModal';
import { SchemaUploadModal } from '../schema/SchemaUploadModal';
import { Badge } from '../common/Badge';

interface QueryStudioProps {
  schemas: SchemaMetadata[];
  selectedSchemaId: number;
  onRefreshSchemas: () => void;
  onAddToast: (type: 'success' | 'error' | 'info', msg: string) => void;
  onRefreshHistory: () => void;
  selectedHistoricalQuery?: QueryHistoryItem | null;
  onOpenDatasetModal?: () => void;
}

export const QueryStudio: React.FC<QueryStudioProps> = ({
  schemas,
  selectedSchemaId,
  onRefreshSchemas,
  onAddToast,
  onRefreshHistory,
  selectedHistoricalQuery,
  onOpenDatasetModal,
}) => {
  const [prompt, setPrompt] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<'table' | 'chart'>('table');

  const [inferenceData, setInferenceData] = useState<QueryGenerateResponse | null>(null);
  const [executionData, setExecutionData] = useState<QueryExecuteResponse | null>(null);
  const [explanationData, setExplanationData] = useState<QueryExplainResponse | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);

  const [selectedModel, setSelectedModel] = useState<string>('querycraft-ultra');
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  const [previewTable, setPreviewTable] = useState<string | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [securityIssues, setSecurityIssues] = useState<string[]>([]);

  const currentSchema = schemas.find((s) => s.id === selectedSchemaId);

  // Load schema tables on schema change
  useEffect(() => {
    if (selectedSchemaId) {
      loadSchemaTables(selectedSchemaId);
    }
  }, [selectedSchemaId]);

  // Handle loading historical or bookmarked query
  useEffect(() => {
    if (selectedHistoricalQuery) {
      setPrompt(selectedHistoricalQuery.natural_language_query);
      setGeneratedSql(selectedHistoricalQuery.generated_sql);
      handleExecuteSQL(selectedHistoricalQuery.generated_sql, selectedHistoricalQuery.natural_language_query);
    }
  }, [selectedHistoricalQuery]);

  const loadSchemaTables = async (schemaId: number) => {
    try {
      const data = await api.getSchemaTables(schemaId);
      setTables(data);
    } catch (err) {
      console.error('Failed to load tables:', err);
    }
  };

  // Dynamically compute prompt templates based on loaded schema/dataset
  const getDynamicPromptTemplates = (): string[] => {
    if (!tables || tables.length === 0) {
      return [
        'Show top 5 customers by total spent',
        'Revenue breakdown by product category',
        'Monthly sales and order volume trend',
      ];
    }

    const firstTbl = tables[0];
    const isEcommerce = tables.some((t) => t.name === 'customers' || t.name === 'order_items');
    if (isEcommerce) {
      return [
        'Show top 5 customers by total spent',
        'Revenue breakdown by product category',
        'Monthly sales and order volume trend',
        'Top rated products with inventory levels',
        'Customer count breakdown by country',
      ];
    }

    // Dynamic prompts tailored for uploaded custom dataset
    const numCols = firstTbl.columns.filter((c) =>
      /int|float|num|real|double|price|amount|salary|rating|score|fare|views|qty|count/i.test(c.type + c.name)
    );
    const catCols = firstTbl.columns.filter((c) =>
      !numCols.some((nc) => nc.name === c.name) && !/date|time/i.test(c.type + c.name)
    );

    const prompts: string[] = [];
    if (catCols.length > 0 && numCols.length > 0) {
      prompts.push(`Show total ${numCols[0].name} by ${catCols[0].name}`);
      prompts.push(`Top 5 ${catCols[0].name} with highest ${numCols[0].name}`);
      prompts.push(`Average ${numCols[0].name} per ${catCols[0].name}`);
    } else if (numCols.length > 0) {
      prompts.push(`Show top 10 records sorted by ${numCols[0].name} highest`);
      prompts.push(`What is the average ${numCols[0].name}?`);
    } else if (catCols.length > 0) {
      prompts.push(`Count of records grouped by ${catCols[0].name}`);
    }
    prompts.push(`Show the first 25 records from ${firstTbl.name}`);
    return prompts.slice(0, 4);
  };

  const samplePromptTemplates = getDynamicPromptTemplates();

  const handleGenerateSQL = async (userPrompt: string = prompt) => {
    if (!userPrompt.trim()) return;
    setIsGenerating(true);
    setStreamingStatus('Initializing model stream...');
    setGeneratedSql('');
    setSecurityIssues([]);
    try {
      const res = await api.generateSQLStream(
        selectedSchemaId,
        userPrompt,
        selectedModel,
        (chunk) => {
          if (chunk.type === 'status' && chunk.message) {
            setStreamingStatus(chunk.message);
          } else if (chunk.type === 'token' && chunk.token) {
            setGeneratedSql((prev) => prev + chunk.token);
          }
        }
      );
      setInferenceData(res);
      setGeneratedSql(res.generated_sql);
      onAddToast('success', `SQL query generated in ${res.inference_time_ms}ms!`);

      // Auto explain plan
      try {
        const exp = await api.explainSQL(res.generated_sql, userPrompt);
        setExplanationData(exp);
      } catch (e) {
        console.warn('Explain failed', e);
      }

      // Auto execute query
      await handleExecuteSQL(res.generated_sql, userPrompt, res.query_id);
      onRefreshHistory();
    } catch (err: any) {
      const errMsg = err.message || err.response?.data?.detail || 'Failed to generate SQL query.';
      onAddToast('error', errMsg);
    } finally {
      setIsGenerating(false);
      setStreamingStatus('');
    }
  };

  const handleExecuteSQL = async (
    sqlToExecute: string = generatedSql,
    nlQuery: string = prompt,
    queryId?: number
  ) => {
    if (!sqlToExecute.trim()) return;
    setIsExecuting(true);
    try {
      const res = await api.executeSQL(selectedSchemaId, sqlToExecute, queryId, nlQuery);
      setExecutionData(res);
      if (res.status === 'SUCCESS') {
        onAddToast('success', `Returned ${res.row_count} rows in ${res.execution_time_ms}ms.`);
        if (inferenceData?.suggested_charts?.length && inferenceData.suggested_charts.includes('bar')) {
          setActiveTab('chart');
        } else {
          setActiveTab('table');
        }
      } else {
        onAddToast('error', res.error_message || 'Query execution failed.');
      }
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || 'Query execution error.';
      onAddToast('error', errMsg);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleValidateSQL = async () => {
    if (!generatedSql.trim()) return;
    try {
      const res = await api.validateSQL(generatedSql);
      if (res.is_read_only && res.is_valid) {
        setSecurityIssues([]);
        onAddToast('success', 'AST Validation: Query is SAFE (Read-Only SELECT).');
      } else {
        setSecurityIssues(res.issues);
        onAddToast('error', `Validation Failed: ${res.issues.join(', ')}`);
      }
    } catch (err: any) {
      onAddToast('error', 'Validation check error.');
    }
  };

  const handleExplainPlan = async () => {
    if (!generatedSql.trim()) return;
    try {
      const exp = await api.explainSQL(generatedSql, prompt);
      setExplanationData(exp);
      onAddToast('info', 'Generated logical query plan.');
    } catch (err) {
      onAddToast('error', 'Failed to generate query explanation.');
    }
  };

  const handleSaveBookmark = async () => {
    if (!generatedSql.trim()) return;
    try {
      const title = prompt.trim() || 'Custom Saved SQL Query';
      await api.saveQuery({
        title,
        natural_language_query: prompt,
        sql_query: generatedSql,
        tags: ['studio'],
        query_id: executionData?.query_id,
      });
      onAddToast('success', `Saved query "${title}" to bookmarks!`);
    } catch (err) {
      onAddToast('error', 'Failed to bookmark query.');
    }
  };

  const handleExportData = async (format: 'csv' | 'xlsx' | 'json') => {
    if (!executionData?.query_id) {
      onAddToast('info', 'Execute a query first to export data.');
      return;
    }
    setIsExporting(true);
    try {
      const blob = await api.exportResults(executionData.query_id, format, `query_export_${Date.now()}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `query_result_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      onAddToast('success', `Exported data as .${format} successfully!`);
    } catch (err: any) {
      onAddToast('error', 'Export download failed.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6 space-y-6">
      {/* Top Banner: Schema info */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-gradient-to-r from-brand-50 via-white to-indigo-50/40 dark:from-brand-950/60 dark:via-slate-900 dark:to-slate-900 border border-brand-500/20 shadow-xl transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-500/20 dark:border-brand-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Natural Language SQL Studio
              <Badge variant="brand">{currentSchema?.name || 'Default DB'}</Badge>
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Ask business questions in plain English — translates to optimized SQL with instant AST safety guarantees.
            </p>
          </div>
        </div>

        {/* Dynamic Suggestion Prompts */}
        <div className="hidden xl:flex items-center gap-2 flex-wrap max-w-2xl justify-end">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" /> Suggested:
          </span>
          {samplePromptTemplates.map((tmpl, idx) => (
            <button
              key={idx}
              onClick={() => {
                setPrompt(tmpl);
                handleGenerateSQL(tmpl);
              }}
              className="px-2.5 py-1 rounded-lg text-xs bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-700/60 transition-colors truncate max-w-[240px] shadow-sm"
              title={tmpl}
            >
              {tmpl}
            </button>
          ))}
        </div>
      </div>

      {/* Main Studio Grid: Left Explorer (1/4) | Right Workspace (3/4) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Schema Browser */}
        <div className="lg:col-span-4 xl:col-span-3 h-[680px]">
          <SchemaExplorer
            currentSchema={currentSchema}
            tables={tables}
            onPreviewTable={(tbl) => setPreviewTable(tbl)}
            onOpenUploadModal={() => setIsUploadModalOpen(true)}
            onOpenDatasetModal={onOpenDatasetModal}
            onSelectColumnSnippet={(tbl, col) => {
              setPrompt((prev) => `${prev} [${tbl}.${col}]`);
            }}
          />
        </div>

        {/* Right Column: Prompt Input, SQL Viewer, Explainer, Results Table & Visualizer */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-6">
          {/* Natural Language Prompt Input Bar */}
          <div className="relative rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl p-4 space-y-3 transition-colors">
            <div className="flex items-center gap-3">
              <div className="flex-1 relative">
                <textarea
                  rows={2}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      handleGenerateSQL();
                    }
                  }}
                  placeholder="Ask a question in plain English (e.g. 'Show total revenue by category', 'Top 5 highest paid', 'Filter where rating > 4.5')..."
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700/80 rounded-xl p-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-brand-500 resize-none font-sans leading-relaxed"
                />
              </div>

              <div className="flex flex-col gap-2">
                <button
                  onClick={() => handleGenerateSQL()}
                  disabled={isGenerating || !prompt.trim()}
                  className="px-5 py-3 rounded-xl font-bold text-xs text-white bg-brand-600 hover:bg-brand-500 active:scale-95 shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isGenerating ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Wand2 className="w-4 h-4" />
                  )}
                  <span>Generate SQL</span>
                </button>

                <button
                  onClick={() => {
                    setPrompt('');
                    setGeneratedSql('');
                    setInferenceData(null);
                    setExecutionData(null);
                    setExplanationData(null);
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700/80 transition-colors flex items-center justify-center gap-1 border border-slate-200 dark:border-transparent"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Clear</span>
                </button>
              </div>
            </div>

            {/* Quick helper tip & Model Engine Selector */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-500 dark:text-slate-400 px-1 pt-1 border-t border-slate-200/60 dark:border-slate-800/60">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-600 dark:text-slate-300">Model Engine:</span>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold px-2.5 py-1 rounded-lg border border-slate-300 dark:border-slate-700/80 focus:outline-none focus:border-brand-500 shadow-sm cursor-pointer"
                >
                  <option value="querycraft-ultra">⚡ QueryCraft Ultra (Streaming SSE)</option>
                  <option value="gemini-flash">🤖 Gemini 1.5 Flash (Cloud)</option>
                  <option value="deepseek-sql">🧠 DeepSeek-Coder SQL (Local)</option>
                </select>
              </div>

              <div className="flex items-center gap-3">
                <span>Press <kbd className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-mono text-[10px]">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-mono text-[10px]">Enter</kbd> to generate</span>
                <span className="hidden sm:inline text-emerald-600 dark:text-emerald-400 font-medium">🛡️ Read-Only Sandboxed</span>
              </div>
            </div>
          </div>

          {/* Security Issue Warnings if any */}
          {securityIssues.length > 0 && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs space-y-1">
              <div className="font-bold flex items-center gap-1.5 text-rose-600 dark:text-rose-400">
                <AlertCircle className="w-4 h-4" /> Query Safety Violation Detected
              </div>
              <ul className="list-disc pl-5 space-y-0.5">
                {securityIssues.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Generated SQL Viewer & Editor */}
          <SQLViewer
            sql={generatedSql}
            onChangeSql={(newSql) => setGeneratedSql(newSql)}
            confidenceScore={inferenceData?.confidence_score}
            inferenceTimeMs={inferenceData?.inference_time_ms}
            isExecuting={isExecuting}
            isStreaming={isGenerating}
            streamingStatus={streamingStatus}
            isCached={inferenceData?.is_cached}
            onExecute={() => handleExecuteSQL(generatedSql, prompt)}
            onValidate={handleValidateSQL}
            onExplain={handleExplainPlan}
            onSaveBookmark={handleSaveBookmark}
          />

          {/* Natural Language Query Explainer */}
          {explanationData && (
            <QueryExplainer
              explanation={explanationData}
              onClose={() => setExplanationData(null)}
            />
          )}

          {/* Results Area (Tabs: Data Grid & Visualizer) */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl overflow-hidden transition-colors">
            {/* Results Header with Table / Chart toggle */}
            <div className="p-4 bg-slate-50 dark:bg-slate-950/70 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('table')}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'table'
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <TableIcon className="w-3.5 h-3.5" />
                  <span>Data Table</span>
                </button>

                <button
                  onClick={() => setActiveTab('chart')}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    activeTab === 'chart'
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Chart Visualizer</span>
                  {inferenceData?.suggested_charts && inferenceData.suggested_charts.length > 0 && (
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  )}
                </button>
              </div>

              {/* Row count & Latency Badge */}
              {executionData && (
                <div className="flex items-center gap-2 text-xs">
                  <Badge variant="success">
                    {executionData.row_count} rows returned
                  </Badge>
                  <Badge variant="brand">
                    {executionData.execution_time_ms} ms
                  </Badge>
                </div>
              )}
            </div>

            {/* Tab Body */}
            <div className="p-4">
              {activeTab === 'table' ? (
                <ResultsTable
                  rows={executionData?.rows || []}
                  columns={executionData?.columns || []}
                  rowCount={executionData?.row_count || 0}
                  executionTimeMs={executionData?.execution_time_ms || 0}
                  onExport={handleExportData}
                  isExporting={isExporting}
                />
              ) : (
                <DataVisualizer
                  rows={executionData?.rows || []}
                  columns={executionData?.columns || []}
                  suggestedCharts={inferenceData?.suggested_charts}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Table Data Preview Modal */}
      <TablePreviewModal
        isOpen={!!previewTable}
        schemaId={selectedSchemaId}
        tableName={previewTable || ''}
        onClose={() => setPreviewTable(null)}
      />

      {/* Schema DDL Upload Modal */}
      <SchemaUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSchemaCreated={() => {
          onRefreshSchemas();
          onAddToast('success', 'Custom schema created successfully!');
        }}
        onSuccessToast={(msg) => onAddToast('success', msg)}
      />
    </div>
  );
};
