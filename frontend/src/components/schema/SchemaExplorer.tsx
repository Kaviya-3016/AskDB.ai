import React, { useState } from 'react';
import {
  Database,
  Table,
  Columns,
  Key,
  Link2,
  Eye,
  Plus,
  Upload,
  Search,
  ChevronRight,
  ChevronDown,
  FileSpreadsheet,
} from 'lucide-react';
import { TableInfo, SchemaMetadata } from '../../types';
import { Badge } from '../common/Badge';

interface SchemaExplorerProps {
  currentSchema?: SchemaMetadata;
  tables: TableInfo[];
  onPreviewTable: (tableName: string) => void;
  onOpenUploadModal: () => void;
  onOpenDatasetModal?: () => void;
  onSelectColumnSnippet?: (tableName: string, colName: string) => void;
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({
  currentSchema,
  tables,
  onPreviewTable,
  onOpenUploadModal,
  onOpenDatasetModal,
  onSelectColumnSnippet,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});

  const toggleTable = (tableName: string) => {
    setExpandedTables((prev) => ({
      ...prev,
      [tableName]: prev[tableName] === undefined ? false : !prev[tableName],
    }));
  };

  const filteredTables = tables.filter((t) => {
    const term = searchTerm.toLowerCase();
    const tableMatch = t.name.toLowerCase().includes(term);
    const colMatch = t.columns.some((c) => c.name.toLowerCase().includes(term));
    return tableMatch || colMatch;
  });

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl flex flex-col h-full overflow-hidden transition-colors">
      {/* Header */}
      <div className="p-4 bg-slate-50 dark:bg-slate-950/70 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-brand-600 dark:text-brand-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Schema Explorer
          </h3>
        </div>

        <div className="flex items-center gap-1.5">
          {onOpenDatasetModal && (
            <button
              onClick={onOpenDatasetModal}
              className="px-2.5 py-1.5 rounded-lg text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 dark:bg-emerald-950/60 hover:bg-emerald-500/20 dark:hover:bg-emerald-900/80 border border-emerald-500/30 dark:border-emerald-500/40 transition-colors flex items-center gap-1 text-xs font-semibold shadow-sm"
              title="Upload CSV / Excel Dataset"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Upload CSV</span>
            </button>
          )}

          <button
            onClick={onOpenUploadModal}
            className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700/60 transition-colors flex items-center gap-1 text-xs"
            title="Upload DDL Schema"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">DDL</span>
          </button>
        </div>
      </div>

      {/* Schema Description & Search */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 space-y-2.5">
        {currentSchema && (
          <div className="text-[11px] text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-950/60 p-2 rounded-lg border border-slate-200 dark:border-slate-800/80">
            <span className="font-semibold text-slate-900 dark:text-slate-200">{currentSchema.name}</span>: {currentSchema.description}
          </div>
        )}

        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            placeholder="Filter tables & columns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      {/* Tables List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredTables.map((table) => {
          const isExpanded = expandedTables[table.name] ?? true;
          return (
            <div
              key={table.name}
              className="rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-950/40 overflow-hidden shadow-sm"
            >
              {/* Table Header Row */}
              <div className="flex items-center justify-between p-2.5 bg-slate-50 dark:bg-slate-900/80 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors">
                <button
                  onClick={() => toggleTable(table.name)}
                  className="flex items-center gap-2 text-left flex-1"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  )}
                  <Table className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                    {table.name}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    ({table.columns.length})
                  </span>
                </button>

                <button
                  onClick={() => onPreviewTable(table.name)}
                  className="p-1 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-700/60 rounded transition-colors"
                  title={`Preview sample data from ${table.name}`}
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Columns Accordion */}
              {isExpanded && (
                <div className="p-2 space-y-1 bg-white dark:bg-slate-950/80 divide-y divide-slate-100 dark:divide-slate-800/40 border-t border-slate-200 dark:border-slate-800/60">
                  {table.columns.map((col) => (
                    <div
                      key={col.name}
                      onClick={() => onSelectColumnSnippet && onSelectColumnSnippet(table.name, col.name)}
                      className="pt-1 first:pt-0 flex items-center justify-between text-[11px] font-mono group cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-900/60 px-1.5 py-0.5 rounded"
                    >
                      <div className="flex items-center gap-1.5">
                        {col.primary_key ? (
                          <span title="Primary Key"><Key className="w-3 h-3 text-amber-500 dark:text-amber-400 shrink-0" /></span>
                        ) : col.foreign_key ? (
                          <span title={`FK -> ${col.foreign_key}`}><Link2 className="w-3 h-3 text-sky-500 dark:text-sky-400 shrink-0" /></span>
                        ) : (
                          <span className="w-3 inline-block" />
                        )}
                        <span className="text-slate-700 dark:text-slate-300 group-hover:text-brand-600 dark:group-hover:text-brand-300 transition-colors">
                          {col.name}
                        </span>
                      </div>

                      <span className="text-[10px] text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-400">
                        {col.type}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {filteredTables.length === 0 && (
          <div className="p-6 text-center text-slate-400 dark:text-slate-500 text-xs">
            No tables matching "{searchTerm}".
          </div>
        )}
      </div>
    </div>
  );
};
