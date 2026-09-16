import React, { useState } from 'react';
import {
  Sparkles,
  Database,
  History,
  Bookmark,
  Sun,
  Moon,
  Shield,
  Layers,
  LogOut,
  User as UserIcon,
  ChevronDown,
  Upload,
  Home,
  Code2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { SchemaMetadata } from '../../types';
import { Badge } from './Badge';

interface NavbarProps {
  schemas: SchemaMetadata[];
  selectedSchemaId: number;
  onSelectSchema: (id: number) => void;
  onOpenHistory: () => void;
  onOpenSaved: () => void;
  onOpenSchemaModal: () => void;
  onOpenDatasetModal?: () => void;
  onOpenAuthModal: () => void;
  currentView: 'auth' | 'home' | 'studio' | 'admin';
  onChangeView: (view: 'auth' | 'home' | 'studio' | 'admin') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  schemas,
  selectedSchemaId,
  onSelectSchema,
  onOpenHistory,
  onOpenSaved,
  onOpenSchemaModal,
  onOpenDatasetModal,
  onOpenAuthModal,
  currentView,
  onChangeView,
}) => {
  const { user, isAuthenticated, logout, demoLogin } = useAuth();
  const { theme, toggleTheme, setTheme } = useTheme();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showDemoMenu, setShowDemoMenu] = useState(false);

  const selectedSchema = schemas.find((s) => s.id === selectedSchemaId);

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between transition-colors duration-200">
      {/* Brand & Schema Picker */}
      <div className="flex items-center gap-6">
        <div
          onClick={() => onChangeView('home')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/25 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-slate-900 via-brand-900 to-indigo-800 dark:from-white dark:via-indigo-100 dark:to-brand-300 bg-clip-text text-transparent">
              QueryCraft <span className="text-brand-600 dark:text-brand-400 font-extrabold">AI</span>
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-brand-500/10 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300 border border-brand-500/20 dark:border-brand-500/30">
              Enterprise
            </span>
          </div>
        </div>

        {/* Schema Switcher */}
        {currentView === 'studio' && (
          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-slate-200 dark:border-slate-800">
            <Layers className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <select
              value={selectedSchemaId}
              onChange={(e) => onSelectSchema(Number(e.target.value))}
              className="bg-slate-100 dark:bg-slate-800 text-sm font-medium text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand-500 transition-colors"
            >
              {schemas.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} {s.is_default ? '(Default Demo DB)' : ''}
                </option>
              ))}
            </select>

            {onOpenDatasetModal && (
              <button
                onClick={onOpenDatasetModal}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 dark:bg-emerald-600/20 hover:bg-emerald-500/20 dark:hover:bg-emerald-600/30 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 dark:border-emerald-500/40 transition-colors shadow-sm"
                title="Upload custom CSV, Excel or JSON dataset"
              >
                <Upload className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Upload Dataset</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Right Controls & User Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* On Home Screen, provide a clean Launch Studio CTA button */}
        {currentView === 'home' && (
          <button
            onClick={() => onChangeView('studio')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-500 shadow-md shadow-brand-500/25 transition-all"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Launch Studio</span>
          </button>
        )}

        {/* History & Saved Queries buttons - Only visible when inside Query Studio / Admin */}
        {currentView !== 'home' && (
          <>
            <button
              onClick={onOpenHistory}
              title="Query History"
              className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all flex items-center gap-1.5 text-sm font-medium"
            >
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">History</span>
            </button>

            <button
              onClick={onOpenSaved}
              title="Bookmarks & Saved Queries"
              className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-all flex items-center gap-1.5 text-sm font-medium"
            >
              <Bookmark className="w-4 h-4" />
              <span className="hidden sm:inline">Saved</span>
            </button>
          </>
        )}

        {/* Unified Theme Button */}
        <button
          onClick={toggleTheme}
          title={`Theme: ${theme === 'dark' ? 'Nightlight (Dark Mode)' : 'Daylight (Light Mode)'} (Click to toggle)`}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600 transition-all flex items-center gap-1.5 text-sm font-medium shadow-sm"
        >
          {theme === 'dark' ? (
            <Moon className="w-4 h-4 text-indigo-400" />
          ) : (
            <Sun className="w-4 h-4 text-amber-500" />
          )}
          <span className="hidden sm:inline">Theme</span>
        </button>

        {/* Auth / Profile Area */}
        {isAuthenticated && user ? (
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-brand-500/20 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold text-xs uppercase">
                {user.full_name.charAt(0)}
              </div>
              <span className="text-sm font-medium text-slate-800 dark:text-slate-200 hidden sm:inline max-w-[120px] truncate">
                {user.full_name}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-2xl p-2 animate-fade-in z-50">
                <div className="px-3 py-2 border-b border-slate-200 dark:border-slate-700/60 mb-1">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Signed in as</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{user.email}</p>
                </div>

                {user.role === 'admin' && (
                  <button
                    onClick={() => {
                      onChangeView('admin');
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/70 flex items-center gap-2"
                  >
                    <Shield className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    Admin Analytics
                  </button>
                )}

                <button
                  onClick={() => {
                    logout();
                    setShowUserMenu(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            {/* Quick 1-Click Demo Login Dropdown - Only visible in Studio/Admin */}
            {currentView !== 'home' && (
              <div className="relative">
                <button
                  onClick={() => setShowDemoMenu(!showDemoMenu)}
                  className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <span>Demo Logins</span>
                  <ChevronDown className="w-3 h-3" />
                </button>

                {showDemoMenu && (
                  <div className="absolute right-0 mt-2 w-48 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-2xl p-1.5 z-50 animate-fade-in">
                    <button
                      onClick={() => {
                        demoLogin('admin');
                        setShowDemoMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-brand-500/10 dark:hover:bg-brand-500/20 hover:text-brand-600 dark:hover:text-brand-300 flex items-center justify-between"
                    >
                      <span>Admin Role</span>
                      <Badge variant="brand">admin</Badge>
                    </button>
                    <button
                      onClick={() => {
                        demoLogin('analyst');
                        setShowDemoMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-brand-500/10 dark:hover:bg-brand-500/20 hover:text-brand-600 dark:hover:text-brand-300 flex items-center justify-between"
                    >
                      <span>Lead Analyst</span>
                      <Badge variant="info">analyst</Badge>
                    </button>
                    <button
                      onClick={() => {
                        demoLogin('viewer');
                        setShowDemoMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-brand-500/10 dark:hover:bg-brand-500/20 hover:text-brand-600 dark:hover:text-brand-300 flex items-center justify-between"
                    >
                      <span>Viewer Role</span>
                      <Badge variant="neutral">viewer</Badge>
                    </button>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={onOpenAuthModal}
              className="px-4 py-1.5 text-sm font-semibold rounded-lg bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-brand-500/25 transition-all"
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
