import React, { useState, useRef } from 'react';
import {
  X,
  Upload,
  FileSpreadsheet,
  FileText,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Database,
  ArrowRight,
  Layers,
} from 'lucide-react';
import { api } from '../../services/api';
import { DatasetUploadResponse } from '../../types';
import { Badge } from '../common/Badge';

interface DatasetUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDatasetUploaded: (datasetData: DatasetUploadResponse) => void;
  onAddToast: (type: 'success' | 'error' | 'info', msg: string) => void;
}

export const DatasetUploadModal: React.FC<DatasetUploadModalProps> = ({
  isOpen,
  onClose,
  onDatasetUploaded,
  onAddToast,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [tableName, setTableName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    const base = file.name.split('.')[0];
    if (!datasetName) setDatasetName(base.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) + ' Data');
    if (!tableName) setTableName(base.toLowerCase().replace(/[^a-z0-9]/g, '_'));
    setError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSampleCSV = (sampleType: 'netflix' | 'salary' | 'crypto') => {
    let csvContent = '';
    let sampleFileName = '';

    if (sampleType === 'netflix') {
      sampleFileName = 'netflix_shows.csv';
      csvContent = `show_id,title,type,director,country,release_year,rating,duration_minutes,genre
s1,Stranger Things,TV Show,Duffer Brothers,United States,2016,TV-MA,50,Sci-Fi & Fantasy
s2,Breaking Bad,TV Show,Vince Gilligan,United States,2008,TV-MA,47,Crime Dramas
s3,Inception,Movie,Christopher Nolan,United States,2010,PG-13,148,Sci-Fi Thriller
s4,Parasite,Movie,Bong Joon-ho,South Korea,2019,R,132,Drama Thriller
s5,The Crown,TV Show,Peter Morgan,United Kingdom,2016,TV-MA,55,Historical Drama
s6,Interstellar,Movie,Christopher Nolan,United States,2014,PG-13,169,Sci-Fi & Space
s7,Squid Game,TV Show,Hwang Dong-hyuk,South Korea,2021,TV-MA,60,Thriller
s8,Spirited Away,Movie,Hayao Miyazaki,Japan,2001,PG,125,Anime Fantasy
s9,The Dark Knight,Movie,Christopher Nolan,United States,2008,PG-13,152,Action & Crime
s10,Money Heist,TV Show,Alex Pina,Spain,2017,TV-MA,45,Crime Thriller
s11,Narcos,TV Show,Chris Brancato,United States,2015,TV-MA,49,Crime Biopic
s12,Whiplash,Movie,Damien Chazelle,United States,2014,R,106,Music Drama`;
    } else if (sampleType === 'salary') {
      sampleFileName = 'employee_salaries.csv';
      csvContent = `emp_id,employee_name,department,job_title,salary,years_experience,performance_score,city
101,Elena Rostova,Engineering,Senior ML Engineer,165000,7,4.9,San Francisco
102,Marcus Vance,Engineering,Backend Developer,135000,5,4.6,New York
103,Sarah Jenkins,Marketing,Growth Marketing Lead,120000,6,4.7,Austin
104,David Kim,Engineering,Staff Infrastructure Engineer,185000,10,5.0,Seattle
105,Priya Sharma,Product,Principal Product Manager,175000,9,4.8,San Francisco
106,Lucas Moreau,Design,Lead UI/UX Designer,130000,6,4.5,New York
107,Aisha Patel,Sales,Enterprise Account Exec,140000,4,4.7,Chicago
108,James Wilson,Finance,Financial Analyst,105000,3,4.3,Boston
109,Carlos Mendez,Marketing,Content Strategist,95000,4,4.4,Austin
110,Rachel Green,Operations,Operations Manager,115000,5,4.6,Denver
111,Kenji Sato,Engineering,Frontend Architect,160000,8,4.9,Seattle
112,Olivia Taylor,Human Resources,HR Director,145000,11,4.8,San Francisco`;
    } else {
      sampleFileName = 'crypto_market_prices.csv';
      csvContent = `coin_symbol,coin_name,price_usd,market_cap_billions,daily_volume_millions,price_change_24h_pct,circulating_supply_millions
BTC,Bitcoin,64250.00,1260.5,28450.0,3.45,19.7
ETH,Ethereum,3450.80,415.2,14200.0,4.12,120.2
SOL,Solana,148.25,68.4,4850.0,-1.20,465.1
BNB,Binance Coin,585.00,87.6,1200.0,0.85,153.8
ADA,Cardano,0.48,17.2,420.0,2.15,35600.0
AVAX,Avalanche,28.50,11.3,580.0,-0.75,395.0
DOT,Polkadot,7.20,10.1,290.0,1.80,1430.0
LINK,Chainlink,14.50,8.5,340.0,5.60,587.0
MATIC,Polygon,0.58,5.7,210.0,1.10,9900.0
NEAR,Near Protocol,5.40,5.9,410.0,6.80,1090.0`;
    }

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const file = new File([blob], sampleFileName, { type: 'text/csv' });
    handleFileChange(file);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select or drop a dataset file first.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const res = await api.uploadDataset(selectedFile, datasetName, tableName);
      onAddToast('success', `Dataset "${res.table_name}" ingested (${res.row_count} rows)!`);
      onDatasetUploaded(res);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to ingest and parse dataset.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] transition-colors">
        {/* Header */}
        <div className="p-6 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/20 dark:border-emerald-500/30">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Upload Real-Time Dataset</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Upload CSV, Excel, or JSON to create a live table and generate SQL queries
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleUploadSubmit} className="p-6 overflow-y-auto space-y-5">
          {error && (
            <div className="p-3 text-xs font-medium rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 1-Click Sample Datasets Bar */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Quick 1-Click Sample Datasets:
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleSampleCSV('netflix')}
                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 hover:bg-brand-500/10 dark:hover:bg-brand-600/20 hover:text-brand-600 dark:hover:text-brand-300 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 transition-all text-left shadow-sm"
              >
                🎬 Netflix Shows (CSV)
              </button>
              <button
                type="button"
                onClick={() => handleSampleCSV('salary')}
                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 hover:bg-brand-500/10 dark:hover:bg-brand-600/20 hover:text-brand-600 dark:hover:text-brand-300 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 transition-all text-left shadow-sm"
              >
                💼 Tech Salaries (CSV)
              </button>
              <button
                type="button"
                onClick={() => handleSampleCSV('crypto')}
                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 hover:bg-brand-500/10 dark:hover:bg-brand-600/20 hover:text-brand-600 dark:hover:text-brand-300 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 transition-all text-left shadow-sm"
              >
                🪙 Crypto Market (CSV)
              </button>
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-brand-500 bg-brand-500/10'
                : selectedFile
                ? 'border-emerald-500/60 bg-emerald-50/50 dark:bg-emerald-950/20'
                : 'border-slate-300 dark:border-slate-700/80 hover:border-brand-500/50 bg-slate-50/50 dark:bg-slate-950/60'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls,.json"
              className="hidden"
              onChange={(e) => e.target.files && e.target.files[0] && handleFileChange(e.target.files[0])}
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">{selectedFile.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {(selectedFile.size / 1024).toFixed(1)} KB • Ready to Ingest
                  </p>
                </div>
                <span className="text-xs text-brand-600 dark:text-brand-400 hover:underline pt-1">
                  Click to choose a different file
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <div className="w-12 h-12 rounded-2xl bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    Drag and drop your dataset file here, or{' '}
                    <span className="text-brand-600 dark:text-brand-400">browse</span>
                  </p>
                  <p className="text-xs text-slate-500 pt-1">
                    Supports .CSV, .XLSX (Excel), and .JSON files up to 50MB
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Dataset Configuration */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Dataset Display Title
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Q3 Sales & Revenue Data"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500 shadow-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                SQL Table Name
              </label>
              <input
                type="text"
                required
                placeholder="e.g. q3_sales_records"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm font-mono text-emerald-700 dark:text-emerald-300 focus:outline-none focus:border-brand-500 shadow-sm"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 active:scale-95 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Ingesting Real-time Dataset...</span>
                </>
              ) : (
                <>
                  <Database className="w-4 h-4" />
                  <span>Ingest & Start Querying</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
