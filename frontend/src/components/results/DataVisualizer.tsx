import React, { useState, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';
import { BarChart3, LineChart, PieChart, Layers } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DataVisualizerProps {
  columns: string[];
  rows: Record<string, any>[];
  suggestedCharts?: string[];
}

export const DataVisualizer: React.FC<DataVisualizerProps> = ({
  columns,
  rows,
  suggestedCharts = ['bar'],
}) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Detect candidate label and value columns
  const candidateLabelCols = useMemo(() => {
    return columns.filter((col) => {
      const sample = rows[0]?.[col];
      return typeof sample === 'string' || col.toLowerCase().includes('date') || col.toLowerCase().includes('month') || col.toLowerCase().includes('name') || col.toLowerCase().includes('country');
    });
  }, [columns, rows]);

  const candidateValueCols = useMemo(() => {
    return columns.filter((col) => {
      const sample = rows[0]?.[col];
      return typeof sample === 'number';
    });
  }, [columns, rows]);

  const [chartType, setChartType] = useState<'bar' | 'line' | 'pie' | 'doughnut'>(
    suggestedCharts.includes('line') ? 'line' : suggestedCharts.includes('pie') ? 'pie' : 'bar'
  );
  const [labelColumn, setLabelColumn] = useState<string>(candidateLabelCols[0] || columns[0] || '');
  const [valueColumn, setValueColumn] = useState<string>(candidateValueCols[0] || columns[1] || '');

  // Prepare chart dataset
  const chartData = useMemo(() => {
    if (!labelColumn || !valueColumn || rows.length === 0) return null;

    const sliceRows = rows.slice(0, 30); // Max 30 points for clarity
    const labels = sliceRows.map((r) => String(r[labelColumn] ?? 'Unknown'));
    const values = sliceRows.map((r) => Number(r[valueColumn] ?? 0));

    const colorPalette = [
      '#6366f1', '#a855f7', '#ec4899', '#06b6d4', '#10b981',
      '#f59e0b', '#3b82f6', '#8b5cf6', '#14b8a6', '#f97316'
    ];

    if (chartType === 'pie' || chartType === 'doughnut') {
      return {
        labels,
        datasets: [
          {
            label: valueColumn,
            data: values,
            backgroundColor: labels.map((_, i) => colorPalette[i % colorPalette.length]),
            borderColor: isDark ? '#0f172a' : '#ffffff',
            borderWidth: 2,
          },
        ],
      };
    }

    if (chartType === 'line') {
      return {
        labels,
        datasets: [
          {
            label: valueColumn,
            data: values,
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.15)',
            borderWidth: 3,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: '#818cf8',
            pointRadius: 4,
          },
        ],
      };
    }

    // Bar chart default
    return {
      labels,
      datasets: [
        {
          label: valueColumn,
          data: values,
          backgroundColor: labels.map((_, i) =>
            i % 2 === 0 ? 'rgba(99, 102, 241, 0.85)' : 'rgba(168, 85, 247, 0.85)'
          ),
          borderRadius: 6,
        },
      ],
    };
  }, [rows, labelColumn, valueColumn, chartType, isDark]);

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: isDark ? '#cbd5e1' : '#475569',
          font: { family: 'Inter', size: 12 },
        },
      },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#ffffff',
        borderColor: isDark ? '#334155' : '#cbd5e1',
        borderWidth: 1,
        titleColor: isDark ? '#ffffff' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#334155',
        padding: 10,
      },
    },
    scales:
      chartType === 'pie' || chartType === 'doughnut'
        ? undefined
        : {
            x: {
              grid: { color: isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
              ticks: { color: isDark ? '#94a3b8' : '#64748b', font: { family: 'Inter', size: 11 } },
            },
            y: {
              grid: { color: isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
              ticks: { color: isDark ? '#94a3b8' : '#64748b', font: { family: 'Inter', size: 11 } },
            },
          },
  };

  if (!chartData || candidateValueCols.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm">
        No numerical metrics detected in the query output for charting.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-xl p-5 animate-fade-in transition-colors">
      {/* Chart Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
        {/* Chart Type Selector */}
        <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-950/80 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setChartType('bar')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              chartType === 'bar'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Bar</span>
          </button>
          <button
            onClick={() => setChartType('line')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              chartType === 'line'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            <span>Line</span>
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              chartType === 'pie'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <PieChart className="w-3.5 h-3.5" />
            <span>Pie</span>
          </button>
          <button
            onClick={() => setChartType('doughnut')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              chartType === 'doughnut'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Doughnut</span>
          </button>
        </div>

        {/* Axes Config */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
            <span>Label:</span>
            <select
              value={labelColumn}
              onChange={(e) => setLabelColumn(e.target.value)}
              className="bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/80 rounded-lg px-2 py-1 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-brand-500 shadow-sm"
            >
              {columns.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
            <span>Metric:</span>
            <select
              value={valueColumn}
              onChange={(e) => setValueColumn(e.target.value)}
              className="bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/80 rounded-lg px-2 py-1 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-brand-500 shadow-sm"
            >
              {candidateValueCols.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Render Canvas */}
      <div className="h-72 sm:h-80 w-full relative">
        {chartType === 'bar' && <Bar data={chartData} options={chartOptions} />}
        {chartType === 'line' && <Line data={chartData} options={chartOptions} />}
        {chartType === 'pie' && <Pie data={chartData} options={chartOptions} />}
        {chartType === 'doughnut' && <Doughnut data={chartData} options={chartOptions} />}
      </div>
    </div>
  );
};
