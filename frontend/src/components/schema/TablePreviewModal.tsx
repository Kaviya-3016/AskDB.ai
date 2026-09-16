import React, { useState, useEffect } from 'react';
import { X, Database, Table, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { TablePreview } from '../../types';
import { Badge } from '../common/Badge';

interface TablePreviewModalProps {
  isOpen: boolean;
  schemaId: number;
  tableName: string;
  onClose: () => void;
}

export const TablePreviewModal: React.FC<TablePreviewModalProps> = ({
  isOpen,
  schemaId,
  tableName,
  onClose,
}) => {
  const [data, setData] = useState<TablePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && tableName) {
      fetchPreview();
    }
  }, [isOpen, schemaId, tableName]);

  const fetchPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.previewTable(schemaId, tableName, 10);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch table preview.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-4xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] transition-colors">
        {/* Header */}
        <div className="p-5 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-500/20 dark:border-brand-500/30">
              <Table className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-white font-mono">{tableName}</h3>
                {data && <Badge variant="brand">{data.total_row_count} total records</Badge>}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Live sample data preview (First 10 records)</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchPreview}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 overflow-auto flex-1">
          {loading ? (
            <div className="py-16 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center justify-center gap-3">
              <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
              <p className="text-xs font-medium">Fetching table preview data...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : data && data.columns.length > 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-x-auto shadow-sm">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider text-[10px]">
                  <tr>
                    {data.columns.map((col) => (
                      <th key={col} className="px-3.5 py-2.5 font-bold">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-800 dark:text-slate-200">
                  {data.sample_rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      {data.columns.map((col) => (
                        <td key={col} className="px-3.5 py-2 whitespace-nowrap">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-400 dark:text-slate-600 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 dark:text-slate-500 text-xs">
              No sample rows found for table '{tableName}'.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
