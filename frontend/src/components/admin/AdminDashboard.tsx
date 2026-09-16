import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  Zap,
  Users,
  Database,
  Cpu,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../services/api';
import { SystemAnalytics, ModelInfo, User, AuditLog } from '../../types';
import { Badge } from '../common/Badge';

export const AdminDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'models' | 'audit'>('overview');

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [anData, mdData, usData, adData] = await Promise.all([
        api.getAdminAnalytics(),
        api.getAdminModels(),
        api.getAdminUsers(),
        api.getAdminAuditLogs(25),
      ]);
      setAnalytics(anData);
      setModelInfo(mdData);
      setUsers(usData);
      setAuditLogs(adData);
    } catch (err) {
      console.error('Failed to load admin telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !analytics) {
    return (
      <div className="py-24 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
        <p className="text-sm font-semibold">Loading Enterprise Telemetry...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in p-4 sm:p-6 transition-colors">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 dark:bg-brand-600/20 text-brand-600 dark:text-brand-400 flex items-center justify-center border border-brand-500/20 dark:border-brand-500/30">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Enterprise Administration & Telemetry</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Real-time observability, model telemetry, security audit logs, and access management</p>
          </div>
        </div>

        <button
          onClick={fetchAdminData}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition-colors flex items-center gap-2 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        {(['overview', 'users', 'models', 'audit'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all ${
              activeTab === tab
                ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/25'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
            }`}
          >
            {tab === 'overview'
              ? 'Platform Overview'
              : tab === 'users'
              ? `Users (${users.length})`
              : tab === 'models'
              ? 'ML Inference Engine'
              : 'Audit Logs'}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && analytics && (
        <div className="space-y-6">
          {/* Metric Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                <span className="font-semibold uppercase tracking-wider">Total Queries</span>
                <Activity className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-white">{analytics.total_queries}</p>
              <div className="flex items-center gap-1.5 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{analytics.successful_queries} succeeded</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                <span className="font-semibold uppercase tracking-wider">Avg Inference Latency</span>
                <Zap className="w-4 h-4 text-amber-500 dark:text-amber-400" />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-white">{analytics.avg_inference_time_ms}ms</p>
              <div className="flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-300 font-medium">
                <span>Target: &lt;200ms (SLO Met)</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                <span className="font-semibold uppercase tracking-wider">Avg DB Execution</span>
                <Clock className="w-4 h-4 text-sky-500 dark:text-sky-400" />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-white">{analytics.avg_execution_time_ms}ms</p>
              <div className="flex items-center gap-1.5 text-[11px] text-sky-600 dark:text-sky-300 font-medium">
                <span>Target: &lt;100ms (High Throughput)</span>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs">
                <span className="font-semibold uppercase tracking-wider">Cache Hit Ratio</span>
                <Cpu className="w-4 h-4 text-purple-500 dark:text-purple-400" />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-white">{analytics.cache_hit_rate}%</p>
              <div className="flex items-center gap-1.5 text-[11px] text-purple-600 dark:text-purple-300 font-medium">
                <span>Redis & In-Memory Layer</span>
              </div>
            </div>
          </div>

          {/* Top Queried Tables & Recent Volume */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <Database className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                Top Queried Relational Tables
              </h3>
              <div className="space-y-3">
                {analytics.top_queried_tables.map((tbl) => (
                  <div key={tbl.table_name} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono text-slate-700 dark:text-slate-300">
                      <span>{tbl.table_name}</span>
                      <span className="text-slate-500 dark:text-slate-400 font-sans">{tbl.query_count} queries</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 dark:bg-slate-950 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-brand-500 to-indigo-400 rounded-full"
                        style={{ width: `${Math.min(100, (tbl.query_count / 150) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Hourly Query Throughput
              </h3>
              <div className="grid grid-cols-7 gap-2 pt-4">
                {analytics.recent_query_volume.map((vol) => (
                  <div key={vol.timestamp} className="flex flex-col items-center gap-2">
                    <div className="w-full bg-slate-50 dark:bg-slate-950 rounded-lg p-2 h-36 flex items-end justify-center border border-slate-100 dark:border-slate-800">
                      <div
                        className="w-full bg-brand-500 rounded-t-md transition-all"
                        style={{ height: `${(vol.queries / 130) * 100}%` }}
                        title={`${vol.queries} queries`}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">{vol.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* USERS TAB */}
      {activeTab === 'users' && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider text-[10px] text-slate-500 dark:text-slate-400">
              <tr>
                <th className="p-4">User ID</th>
                <th className="p-4">Name</th>
                <th className="p-4">Email</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
                <th className="p-4">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-800 dark:text-slate-200">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="p-4 font-mono text-slate-400 dark:text-slate-500">#{u.id}</td>
                  <td className="p-4 font-semibold text-slate-900 dark:text-white">{u.full_name}</td>
                  <td className="p-4 font-mono text-slate-600 dark:text-slate-300">{u.email}</td>
                  <td className="p-4">
                    <Badge variant={u.role === 'admin' ? 'brand' : u.role === 'analyst' ? 'info' : 'neutral'}>
                      {u.role}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      Active
                    </span>
                  </td>
                  <td className="p-4 text-slate-500 dark:text-slate-400">{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* MODELS TAB */}
      {activeTab === 'models' && modelInfo && (
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">{modelInfo.model_name}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">{modelInfo.architecture}</p>
            </div>
            <Badge variant="success">{modelInfo.status}</Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
              <span className="text-xs text-slate-500 dark:text-slate-400">Deployed Version</span>
              <p className="text-sm font-bold text-slate-900 dark:text-white font-mono">{modelInfo.version}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
              <span className="text-xs text-slate-500 dark:text-slate-400">Average Latency</span>
              <p className="text-sm font-bold text-amber-600 dark:text-amber-400 font-mono">{modelInfo.average_latency_ms} ms</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
              <span className="text-xs text-slate-500 dark:text-slate-400">Fallback Engine</span>
              <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400 font-mono">{modelInfo.fallback_engine}</p>
            </div>
          </div>
        </div>
      )}

      {/* AUDIT LOGS TAB */}
      {activeTab === 'audit' && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider text-[10px] text-slate-500 dark:text-slate-400">
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">Action</th>
                <th className="p-4">User</th>
                <th className="p-4">Resource</th>
                <th className="p-4">IP Address</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px] text-slate-800 dark:text-slate-200">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="p-4 text-slate-500 dark:text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="p-4 font-bold text-brand-600 dark:text-brand-400">{log.action}</td>
                  <td className="p-4 text-slate-700 dark:text-slate-300 font-sans">{log.user_email || 'Anonymous'}</td>
                  <td className="p-4 text-slate-500 dark:text-slate-400">{log.resource}</td>
                  <td className="p-4 text-slate-400 dark:text-slate-500">{log.ip_address || '127.0.0.1'}</td>
                  <td className="p-4 font-sans">
                    <Badge variant={log.status === 'SUCCESS' ? 'success' : 'danger'}>
                      {log.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
