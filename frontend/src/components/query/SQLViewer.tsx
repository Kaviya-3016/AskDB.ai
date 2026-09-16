import React, { useState } from 'react';
import {
  Play,
  Copy,
  Check,
  Edit3,
  ShieldCheck,
  Bookmark,
  Sparkles,
  Info,
  Code2,
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface SQLViewerProps {
  sql: string;
  onChangeSql: (sql: string) => void;
  onExecute: () => void;
  onValidate: () => void;
  onExplain: () => void;
  onSaveBookmark: () => void;
  isExecuting: boolean;
  isStreaming?: boolean;
  streamingStatus?: string;
  confidenceScore?: number;
  inferenceTimeMs?: number;
  isCached?: boolean;
}

export const SQLViewer: React.FC<SQLViewerProps> = ({
  sql,
  onChangeSql,
  onExecute,
  onValidate,
  onExplain,
  onSaveBookmark,
  isExecuting,
  isStreaming = false,
  streamingStatus,
  confidenceScore,
  inferenceTimeMs,
  isCached,
}) => {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Syntax highlight robust single-pass token tokenizer
  const highlightSQL = (code: string) => {
    if (!code) return '';

    const escapeHtml = (str: string) =>
      str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    const tokenRegex =
      /('(?:''|[^'])*')|(\b(?:SELECT|FROM|WHERE|GROUP BY|ORDER BY|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|ON|AND|OR|AS|DESC|ASC|LIMIT|COUNT|SUM|AVG|MIN|MAX|ROUND|CASE|WHEN|THEN|ELSE|END|HAVING|DISTINCT|STRFTIME|NOT|NULL|IN|LIKE|BETWEEN|IS)\b)|(\b\d+(?:\.\d+)?\b)|([<>=!+*/-]+)/gi;

    return code.replace(
      tokenRegex,
      (match, stringLiteral, keyword, numberLiteral, operator) => {
        if (stringLiteral) {
          return `<span class="text-emerald-300">${escapeHtml(stringLiteral)}</span>`;
        }
        if (keyword) {
          return `<span class="text-indigo-400 font-bold">${escapeHtml(keyword.toUpperCase())}</span>`;
        }
        if (numberLiteral) {
          return `<span class="text-amber-300 font-medium">${escapeHtml(numberLiteral)}</span>`;
        }
        if (operator) {
          return `<span class="text-cyan-400">${escapeHtml(operator)}</span>`;
        }
        return escapeHtml(match);
      }
    );
  };

  const lines = sql.split('\n');

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl overflow-hidden transition-colors">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-slate-50 dark:bg-slate-950/70 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Generated SQL
            </span>
          </div>

          {isStreaming ? (
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-brand-500/20 text-brand-700 dark:text-brand-300 border border-brand-500/40 animate-pulse">
              <Sparkles className="w-3 h-3 text-brand-600 dark:text-brand-400 animate-spin" />
              <span>{streamingStatus || 'Streaming AST Tokens...'}</span>
            </span>
          ) : confidenceScore !== undefined ? (
            <Badge
              variant={confidenceScore >= 0.9 ? 'success' : confidenceScore >= 0.75 ? 'info' : 'warning'}
            >
              {Math.round(confidenceScore * 100)}% Confidence
            </Badge>
          ) : null}

          {inferenceTimeMs !== undefined && !isStreaming && (
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              ⚡ {inferenceTimeMs}ms {isCached ? '(Cached)' : ''}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              isEditing
                ? 'bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-300 border-brand-500/40'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700/60 shadow-sm'
            }`}
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>{isEditing ? 'Editing Mode' : 'Edit SQL'}</span>
          </button>

          <button
            onClick={onExplain}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700/60 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Info className="w-3.5 h-3.5 text-sky-500 dark:text-sky-400" />
            <span>Explain Plan</span>
          </button>

          <button
            onClick={onSaveBookmark}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700/60 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Bookmark className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
            <span>Save Query</span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700/60 transition-colors shadow-sm"
            title="Copy SQL"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-500 dark:text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={onExecute}
            disabled={isExecuting || !sql.trim()}
            className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 active:scale-95 shadow-lg shadow-emerald-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isExecuting ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>Execute SQL</span>
          </button>
        </div>
      </div>

      {/* Code Display Area */}
      <div className="relative font-mono text-xs sm:text-sm bg-slate-950 p-4 overflow-x-auto min-h-[140px] max-h-[300px]">
        {isEditing ? (
          <textarea
            value={sql}
            onChange={(e) => onChangeSql(e.target.value)}
            className="w-full h-full min-h-[120px] bg-transparent text-emerald-300 font-mono text-xs sm:text-sm border-none outline-none resize-y leading-relaxed focus:ring-0"
            spellCheck={false}
          />
        ) : (
          <div className="flex gap-4">
            {/* Line numbers */}
            <div className="select-none text-right text-slate-600 pr-2 border-r border-slate-800/60 font-mono">
              {lines.map((_, i) => (
                <div key={i} className="leading-relaxed">
                  {i + 1}
                </div>
              ))}
            </div>
            {/* Code lines */}
            <div className="flex-1 text-slate-200 leading-relaxed font-mono whitespace-pre flex items-baseline">
              <span dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }} />
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-brand-400 ml-1 rounded-sm animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Security Badge */}
      <div className="px-5 py-2 bg-slate-50 dark:bg-slate-950/90 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
          <span>AST Safe Execution Engine: Read-only SELECT sandboxing active</span>
        </div>
        <button
          onClick={onValidate}
          className="text-brand-600 dark:text-brand-400 hover:text-brand-500 dark:hover:text-brand-300 transition-colors font-semibold"
        >
          Inspect AST Security Report →
        </button>
      </div>
    </div>
  );
};
