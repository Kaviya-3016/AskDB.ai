import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Database,
  Upload,
  Shield,
  BarChart3,
  Zap,
  CheckCircle2,
  FileSpreadsheet,
  Code2,
  Layers,
  Cpu,
  Lock,
  Play,
  FileCode,
  Table,
  Check,
  TrendingUp,
} from 'lucide-react';
import { SchemaMetadata } from '../../types';
import { Badge } from '../common/Badge';

interface HomePageProps {
  schemas: SchemaMetadata[];
  onLaunchStudio: (schemaId?: number, initialPrompt?: string) => void;
  onOpenDatasetModal: () => void;
  onOpenAuthModal: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  schemas,
  onLaunchStudio,
  onOpenDatasetModal,
  onOpenAuthModal,
}) => {
  const [demoPromptIndex, setDemoPromptIndex] = useState(0);

  const demoExamples = [
    {
      schema: 'E-Commerce & Orders DB',
      schemaId: 1,
      prompt: 'Show top 5 customers with their total spending on completed orders',
      sql: `SELECT c.first_name, c.last_name, SUM(o.total_amount) AS total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE o.status = 'DELIVERED'\nGROUP BY c.customer_id, c.first_name, c.last_name\nORDER BY total_spent DESC\nLIMIT 5;`,
      metrics: '5 rows • 14ms execution',
      confidence: '98% Confidence',
    },
    {
      schema: 'Tech Salaries & Employees',
      schemaId: 2,
      prompt: 'Find average salary by department where experience is over 5 years',
      sql: `SELECT department, AVG(salary) AS avg_salary, COUNT(*) AS employee_count\nFROM employee_salaries\nWHERE years_experience > 5\nGROUP BY department\nORDER BY avg_salary DESC;`,
      metrics: '4 departments • 9ms execution',
      confidence: '96% Confidence',
    },
    {
      schema: 'Netflix Shows & Movies',
      schemaId: 3,
      prompt: 'Count total titles released by genre after 2015',
      sql: `SELECT genre, COUNT(*) AS title_count\nFROM netflix_shows\nWHERE release_year > 2015\nGROUP BY genre\nORDER BY title_count DESC;`,
      metrics: '6 genres • 11ms execution',
      confidence: '95% Confidence',
    },
  ];

  const currentExample = demoExamples[demoPromptIndex];

  return (
    <div className="space-y-20 pb-20 animate-fade-in">
      {/* HERO SECTION */}
      <section className="relative pt-12 sm:pt-20 px-4 max-w-7xl mx-auto text-center space-y-8">
        {/* Glow background accent */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 sm:w-[600px] h-96 bg-brand-500/15 dark:bg-brand-500/20 rounded-full blur-3xl pointer-events-none -z-10" />

        {/* Announcement Chip */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 dark:bg-brand-500/20 border border-brand-500/30 text-brand-700 dark:text-brand-300 text-xs font-semibold shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
          <span>Next-Gen Enterprise NLP to SQL Generator & Real-Time Data Ingestion</span>
        </div>

        {/* Hero Title */}
        <div className="space-y-4 max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.1]">
            Turn Plain English into{' '}
            <span className="bg-gradient-to-r from-brand-600 via-indigo-600 to-pink-500 dark:from-brand-400 dark:via-indigo-300 dark:to-pink-400 bg-clip-text text-transparent">
              Production SQL
            </span>{' '}
            Instantly.
          </h1>
          <p className="text-base sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Query relational databases and uploaded datasets (CSV, Excel, JSON) using natural language.
            Features AST sandboxing, query plan explainers, real-time Chart.js visualizers, and multi-dialect translation.
          </p>
        </div>

        {/* Call to Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={() => onLaunchStudio()}
            className="px-6 sm:px-8 py-3.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-sm sm:text-base shadow-xl shadow-brand-500/30 hover:shadow-brand-500/40 active:scale-95 transition-all flex items-center gap-2.5 group"
          >
            <span>Launch Query Studio</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={onOpenDatasetModal}
            className="px-6 sm:px-8 py-3.5 rounded-2xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 font-bold text-sm sm:text-base border border-slate-300 dark:border-slate-700 shadow-md active:scale-95 transition-all flex items-center gap-2.5"
          >
            <Upload className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Upload Real-Time Dataset</span>
          </button>
        </div>

        {/* Trust & Spec Badges */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>AST Safe SELECT Sandboxing</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>Sub-20ms DB Latency</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>PostgreSQL, SQLite, MySQL</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>CSV / XLSX Ingestion</span>
          </div>
        </div>

        {/* INTERACTIVE DEMO SANDBOX CARD */}
        <div className="pt-8 max-w-4xl mx-auto text-left">
          <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 shadow-2xl overflow-hidden backdrop-blur-xl">
            {/* Window bar */}
            <div className="px-5 py-3.5 bg-slate-100 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-xs font-mono text-slate-500 ml-2">live-query-synthesizer.sql</span>
              </div>

              {/* Sample Tabs */}
              <div className="flex items-center gap-1.5">
                {demoExamples.map((ex, idx) => (
                  <button
                    key={idx}
                    onClick={() => setDemoPromptIndex(idx)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
                      demoPromptIndex === idx
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800'
                    }`}
                  >
                    Sample {idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Prompt input preview */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60">
              <div className="text-[11px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> English Question
              </div>
              <p className="text-sm sm:text-base font-semibold text-slate-900 dark:text-white">
                "{currentExample.prompt}"
              </p>
            </div>

            {/* Code output preview */}
            <div className="p-5 bg-slate-950 text-slate-100 font-mono text-xs sm:text-sm overflow-x-auto space-y-3">
              <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800 text-slate-400 font-sans">
                <span className="text-emerald-400 font-semibold">{currentExample.confidence}</span>
                <span>{currentExample.metrics}</span>
              </div>
              <pre className="text-emerald-300 leading-relaxed font-mono whitespace-pre">
                {currentExample.sql}
              </pre>
            </div>

            {/* Bottom action trigger */}
            <div className="p-4 bg-slate-100 dark:bg-slate-950/80 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                Active Schema: <strong className="text-slate-900 dark:text-slate-200">{currentExample.schema}</strong>
              </span>
              <button
                onClick={() => onLaunchStudio(undefined, currentExample.prompt)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-600/30 flex items-center gap-1.5 transition-all"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Try This In Query Studio</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURE PILLARS GRID */}
      <section className="max-w-7xl mx-auto px-4 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="brand">Enterprise Architecture</Badge>
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 dark:text-white">
            Engineered for Precision, Safety & Performance
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            A battle-tested stack combining natural language inference, semantic schema indexing, and safe AST query execution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-brand-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-500/20">
              <Code2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Semantic AST Synthesizer</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Dynamically parses schemas to infer column mappings, joins, aggregations (SUM, AVG, COUNT), and filter clauses with high precision.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-emerald-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 dark:bg-emerald-600/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/20">
              <Upload className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Live Multi-Format Datasets</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Upload any CSV, Excel (.xlsx/.xls), or JSON file. Creates sandbox tables on-the-fly and generates targeted SQL queries immediately.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-amber-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 dark:bg-amber-600/20 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-500/20">
              <Shield className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Zero-Trust SQL Sandboxing</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              AST security verification strictly enforces read-only operations, blocking any destructive queries (DROP, DELETE, TRUNCATE, ALTER).
            </p>
          </div>

          {/* Card 4 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-indigo-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 dark:bg-indigo-600/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center border border-indigo-500/20">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Visual Analytics Engine</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Auto-detects numeric metrics and categorical dimensions to render responsive Bar, Line, Pie, and Doughnut charts powered by Chart.js.
            </p>
          </div>

          {/* Card 5 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-purple-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 dark:bg-purple-600/20 text-purple-600 dark:text-purple-400 flex items-center justify-center border border-purple-500/20">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">High-Throughput Caching</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              In-memory and Redis-ready caching layer provides instant response times for recurring business queries and high-traffic analytics.
            </p>
          </div>

          {/* Card 6 */}
          <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 shadow-lg hover:border-sky-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 dark:bg-sky-600/20 text-sky-600 dark:text-sky-400 flex items-center justify-center border border-sky-500/20">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Enterprise Access & Audit</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Role-based access controls for Admins, Analysts, and Viewers with comprehensive telemetry and audit logs for compliance.
            </p>
          </div>
        </div>
      </section>

      {/* 4-STEP WORKFLOW */}
      <section className="max-w-7xl mx-auto px-4 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="info">Simple 4-Step Flow</Badge>
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 dark:text-white">
            From Natural Language to Business Insights
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3 relative">
            <span className="text-3xl font-black text-brand-600 dark:text-brand-400">01</span>
            <h4 className="text-base font-bold text-slate-900 dark:text-white">Select or Upload Dataset</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Choose an existing database schema or upload a custom CSV/Excel/JSON file.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3 relative">
            <span className="text-3xl font-black text-indigo-600 dark:text-indigo-400">02</span>
            <h4 className="text-base font-bold text-slate-900 dark:text-white">Ask in Plain English</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Type questions like "Which department has highest average compensation?".
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3 relative">
            <span className="text-3xl font-black text-amber-600 dark:text-amber-400">03</span>
            <h4 className="text-base font-bold text-slate-900 dark:text-white">Inspect AST & Execute</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Review confidence score, syntax highlighting, and click Execute to run the sandbox query.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3 relative">
            <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400">04</span>
            <h4 className="text-base font-bold text-slate-900 dark:text-white">Visualize & Export</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Render interactive charts or export formatted results directly to CSV, Excel, or JSON.
            </p>
          </div>
        </div>
      </section>

      {/* QUICK PRE-LOADED DATASETS */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Explore Ready-to-Query Datasets</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">Jump right into pre-seeded schemas and real-time datasets</p>
          </div>
          <button
            onClick={onOpenDatasetModal}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-2 shadow-md shadow-emerald-600/30 transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Custom Dataset</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {schemas.map((schema) => (
            <div
              key={schema.id}
              className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-md hover:shadow-xl transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Badge variant="brand">{schema.dialect.toUpperCase()}</Badge>
                  {(() => {
                    try {
                      const tbls = JSON.parse(schema.schema_json || '[]');
                      return (
                        <span className="text-xs font-mono text-slate-500">
                          {Array.isArray(tbls) ? `${tbls.length} tables` : 'Live DB'}
                        </span>
                      );
                    } catch {
                      return <span className="text-xs font-mono text-slate-500">Live DB</span>;
                    }
                  })()}
                </div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white">{schema.name}</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                  {schema.description || 'Relational dataset ready for natural language querying.'}
                </p>
              </div>

              <button
                onClick={() => onLaunchStudio(schema.id)}
                className="w-full py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-brand-600 hover:text-white text-slate-800 dark:text-slate-200 font-semibold text-xs flex items-center justify-center gap-2 transition-all border border-slate-200 dark:border-slate-700"
              >
                <span>Query This Dataset</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* CTA BANNER */}
      <section className="max-w-7xl mx-auto px-4">
        <div className="rounded-3xl bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-700 p-8 sm:p-12 text-white text-center space-y-6 shadow-2xl relative overflow-hidden">
          <div className="space-y-3 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
              Ready to Accelerate Your Data Workflow?
            </h2>
            <p className="text-sm sm:text-base text-white/80">
              Start querying in seconds with zero SQL syntax friction and complete security.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => onLaunchStudio()}
              className="px-8 py-3.5 rounded-2xl bg-white text-brand-700 hover:bg-slate-100 font-bold text-sm shadow-xl active:scale-95 transition-all flex items-center gap-2"
            >
              <span>Open Query Studio</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onOpenAuthModal}
              className="px-8 py-3.5 rounded-2xl bg-brand-900/60 hover:bg-brand-900 text-white font-bold text-sm border border-white/20 active:scale-95 transition-all"
            >
              Sign In / Demo Accounts
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
