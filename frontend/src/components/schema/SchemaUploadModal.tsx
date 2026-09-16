import React, { useState } from 'react';
import { X, UploadCloud, Database, Code, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';
import { SchemaMetadata } from '../../types';

interface SchemaUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSchemaCreated: (newSchema: SchemaMetadata) => void;
  onSuccessToast: (msg: string) => void;
}

export const SchemaUploadModal: React.FC<SchemaUploadModalProps> = ({
  isOpen,
  onClose,
  onSchemaCreated,
  onSuccessToast,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dialect, setDialect] = useState('postgres');
  const [ddlContent, setDdlContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSampleTemplate = () => {
    setName('Healthcare Patients & Visits DB');
    setDescription('Clinical patients records, appointments, doctors, and treatments.');
    setDialect('postgres');
    setDdlContent(`CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    blood_group VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    consultation_fee NUMERIC(10, 2) NOT NULL
);

CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'SCHEDULED',
    diagnosis TEXT
);`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const created = await api.uploadSchema({
        name,
        description,
        dialect,
        ddl_content: ddlContent,
      });
      onSchemaCreated(created);
      onSuccessToast(`Schema "${created.name}" created successfully!`);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse and upload DDL schema.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden transition-colors">
        {/* Header */}
        <div className="p-6 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 dark:bg-brand-600/20 border border-brand-500/20 dark:border-brand-500/30 flex items-center justify-center text-brand-600 dark:text-brand-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Import Custom Database Schema</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Paste standard SQL DDL CREATE TABLE statements</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-xs font-medium rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Schema Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Sales & Logistics DB"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500 shadow-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">SQL Dialect</label>
              <select
                value={dialect}
                onChange={(e) => setDialect(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500 shadow-sm"
              >
                <option value="postgres">PostgreSQL</option>
                <option value="sqlite">SQLite</option>
                <option value="mysql">MySQL</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Description (Optional)</label>
            <input
              type="text"
              placeholder="Short description of schema domain and business context..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500 shadow-sm"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">DDL Statements</label>
              <button
                type="button"
                onClick={handleSampleTemplate}
                className="text-xs text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1 font-medium"
              >
                <span>Load Sample Healthcare DDL</span>
              </button>
            </div>
            <textarea
              required
              rows={8}
              value={ddlContent}
              onChange={(e) => setDdlContent(e.target.value)}
              placeholder="CREATE TABLE table_name (&#10;    id INT PRIMARY KEY,&#10;    name VARCHAR(100) NOT NULL&#10;);"
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-3 text-xs font-mono text-emerald-700 dark:text-emerald-300 focus:outline-none focus:border-brand-500 leading-relaxed resize-none shadow-sm"
            />
          </div>

          {/* Actions */}
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
              disabled={isSubmitting || !name.trim() || !ddlContent.trim()}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-500 active:scale-95 shadow-lg shadow-brand-500/25 transition-all disabled:opacity-50"
            >
              {isSubmitting ? 'Parsing & Saving...' : 'Create Schema'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
