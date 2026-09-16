import React, { useState } from 'react';
import { X, Bookmark, Tag, Star, Play, Search } from 'lucide-react';
import { SavedQuery } from '../../types';
import { Badge } from '../common/Badge';

interface SavedQueriesModalProps {
  isOpen: boolean;
  savedQueries: SavedQuery[];
  onClose: () => void;
  onSelectQuery: (nl: string, sql: string) => void;
}

export const SavedQueriesModal: React.FC<SavedQueriesModalProps> = ({
  isOpen,
  savedQueries,
  onClose,
  onSelectQuery,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const filteredQueries = savedQueries.filter((q) => {
    const term = searchTerm.toLowerCase();
    return (
      q.title.toLowerCase().includes(term) ||
      q.natural_language_query.toLowerCase().includes(term) ||
      q.tags.some((t) => t.toLowerCase().includes(term))
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] transition-colors">
        {/* Header */}
        <div className="p-5 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-500/20 dark:border-amber-500/30">
              <Bookmark className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Saved & Bookmarked Queries</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">{savedQueries.length} saved workflows</p>
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
              placeholder="Search saved queries by title or tag..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-brand-500 shadow-sm"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredQueries.length > 0 ? (
            filteredQueries.map((query) => (
              <div
                key={query.id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/60 hover:border-amber-500/40 transition-all space-y-2 group shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4 text-amber-500 dark:text-amber-400 fill-amber-500 dark:fill-amber-400" />
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">{query.title}</h4>
                  </div>
                  <button
                    onClick={() => {
                      onSelectQuery(query.natural_language_query, query.sql_query);
                      onClose();
                    }}
                    className="px-3 py-1 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-md shadow-brand-600/20"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    Load Query
                  </button>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 italic">
                  "{query.natural_language_query}"
                </p>

                <pre className="p-2.5 rounded-lg bg-slate-900 text-[11px] font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap max-h-24 border border-slate-800/80">
                  {query.sql_query}
                </pre>

                {query.tags && query.tags.length > 0 && (
                  <div className="flex items-center gap-1.5 pt-1">
                    <Tag className="w-3 h-3 text-slate-400 dark:text-slate-500" />
                    {query.tags.map((tag, idx) => (
                      <Badge key={idx} variant="neutral" size="sm">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-xs">
              No saved bookmarks found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
