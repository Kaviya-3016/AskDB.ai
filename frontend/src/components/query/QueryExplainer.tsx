import React from 'react';
import { QueryExplainResponse } from '../../types';
import { Info, Database, Filter, Layers, ListOrdered, CheckCircle, X } from 'lucide-react';

interface QueryExplainerProps {
  explanation: QueryExplainResponse | null;
  onClose: () => void;
}

export const QueryExplainer: React.FC<QueryExplainerProps> = ({ explanation, onClose }) => {
  if (!explanation) return null;

  return (
    <div className="rounded-2xl border border-sky-200 dark:border-sky-900/60 bg-sky-50/70 dark:bg-sky-950/20 p-5 backdrop-blur-md animate-fade-in shadow-xl relative transition-colors">
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-600 dark:text-sky-400 flex items-center justify-center">
          <Info className="w-4 h-4" />
        </div>
        <h4 className="text-sm font-bold text-sky-900 dark:text-sky-200">Query Plan & Logical Breakdown</h4>
      </div>

      <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 mb-4 leading-relaxed font-medium bg-white dark:bg-slate-900/60 p-3 rounded-xl border border-sky-100 dark:border-slate-800 shadow-sm">
        {explanation.summary}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Step by step operations */}
        <div className="space-y-2">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-sky-700 dark:text-sky-400 flex items-center gap-1.5">
            <ListOrdered className="w-3.5 h-3.5" /> Operations Pipeline
          </span>
          <ul className="space-y-1.5">
            {explanation.operations.map((op, idx) => (
              <li key={idx} className="flex items-start gap-2 text-slate-700 dark:text-slate-300">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{op}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Tables & Filters metadata */}
        <div className="space-y-3">
          {explanation.tables_involved.length > 0 && (
            <div>
              <span className="font-semibold uppercase tracking-wider text-[11px] text-indigo-700 dark:text-indigo-400 flex items-center gap-1.5 mb-1.5">
                <Database className="w-3.5 h-3.5" /> Tables Referenced
              </span>
              <div className="flex flex-wrap gap-1.5">
                {explanation.tables_involved.map((tbl, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-800/80 text-indigo-800 dark:text-indigo-200 font-mono text-[11px]"
                  >
                    {tbl}
                  </span>
                ))}
              </div>
            </div>
          )}

          {explanation.filter_conditions.length > 0 && (
            <div>
              <span className="font-semibold uppercase tracking-wider text-[11px] text-amber-700 dark:text-amber-400 flex items-center gap-1.5 mb-1.5">
                <Filter className="w-3.5 h-3.5" /> Predicate Filters
              </span>
              <div className="flex flex-wrap gap-1.5">
                {explanation.filter_conditions.map((f, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/80 border border-amber-200 dark:border-amber-800/60 text-amber-800 dark:text-amber-200 font-mono text-[11px]"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
