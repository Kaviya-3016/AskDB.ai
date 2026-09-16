import React, { useState } from 'react';
import {
  X,
  History,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  Search,
  Play,
  Trash2,
} from 'lucide-react';
import { QueryHistoryItem } from '../../types';
import { Badge } from '../common/Badge';

interface HistoryDrawerProps {
  isOpen: boolean;
  historyItems: QueryHistoryItem[];
  onClose: () => void;
  onSelectQuery: (item: QueryHistoryItem) => void;
  onDeleteHistoryItem: (id: number) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  historyItems,
  onClose,
  onSelectQuery,
  onDeleteHistoryItem,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const filteredHistory = historyItems.filter((h) => {
    const term = searchTerm.toLowerCase();
    return (
      h.natural_language_query.toLowerCase().includes(term) ||
      h.generated_sql.toLowerCase().includes(term)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 h-full flex flex-col shadow-2xl transition-colors">
        {/* Drawer Header */}
        <div className="p-5 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-500/20 dark:border-brand-500/30">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Query Execution History</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">{historyItems.length} total recorded runs</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400 dark:text-slate-500" />
            <input
              type="text"
              placeholder="Search historical queries & SQL..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-brand-500 shadow-sm"
            />
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredHistory.length > 0 ? (
            filteredHistory.map((item) => (
              <div
                key={item.id}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/60 hover:border-brand-500/40 transition-all space-y-2 group shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {item.status === 'SUCCESS' ? (
                      <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                    )}
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 line-clamp-1">
                      {item.natural_language_query}
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        onSelectQuery(item);
                        onClose();
                      }}
                      className="p-1 rounded text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      title="Load and re-execute"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                    <button
                      onClick={() => onDeleteHistoryItem(item.id)}
                      className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      title="Delete entry"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <pre className="p-2.5 rounded-lg bg-slate-900 text-[11px] font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap max-h-20 border border-slate-800/80">
                  {item.generated_sql}
                </pre>

                <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.execution_time_ms}ms
                    </span>
                    {item.is_cached && (
                      <Badge variant="brand" size="sm">
                        Cached
                      </Badge>
                    )}
                  </div>
                  <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-xs">
              No query history found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
