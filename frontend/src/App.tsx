import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Navbar } from './components/common/Navbar';
import { Toast, ToastProps } from './components/common/Toast';
import { HomePage } from './components/home/HomePage';
import { QueryStudio } from './components/query/QueryStudio';
import { AdminDashboard } from './components/admin/AdminDashboard';
import { HistoryDrawer } from './components/history/HistoryDrawer';
import { SavedQueriesModal } from './components/history/SavedQueriesModal';
import { AuthModal } from './components/auth/AuthModal';
import { GoogleAuthPage } from './components/auth/GoogleAuthPage';
import { DatasetUploadModal } from './components/schema/DatasetUploadModal';
import { api } from './services/api';
import { SchemaMetadata, SavedQuery, QueryHistoryItem, DatasetUploadResponse } from './types';

const MainApp: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<'auth' | 'home' | 'studio' | 'admin'>('home');
  const [pendingLaunchIntent, setPendingLaunchIntent] = useState<{ schemaId?: number; initialPrompt?: string } | null>(null);
  const [schemas, setSchemas] = useState<SchemaMetadata[]>([]);
  const [selectedSchemaId, setSelectedSchemaId] = useState<number>(1);
  const [historyItems, setHistoryItems] = useState<QueryHistoryItem[]>([]);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [selectedHistoricalQuery, setSelectedHistoricalQuery] = useState<QueryHistoryItem | null>(null);

  // Modal states
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isSavedOpen, setIsSavedOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [toasts, setToasts] = useState<Array<Omit<ToastProps, 'onClose'>>>([]);

  // When user completes authentication on auth page, smoothly transition to Studio / Workspace
  useEffect(() => {
    if (isAuthenticated && currentView === 'auth') {
      if (pendingLaunchIntent) {
        if (pendingLaunchIntent.schemaId) setSelectedSchemaId(pendingLaunchIntent.schemaId);
        if (pendingLaunchIntent.initialPrompt) {
          setSelectedHistoricalQuery({
            id: 0,
            schema_id: pendingLaunchIntent.schemaId || selectedSchemaId,
            natural_language_query: pendingLaunchIntent.initialPrompt,
            generated_sql: '',
            confidence_score: 0.95,
            status: 'SUCCESS',
            execution_time_ms: 0,
            is_cached: false,
            created_at: new Date().toISOString(),
          });
        }
        setPendingLaunchIntent(null);
      }
      setCurrentView('studio');
    }
  }, [isAuthenticated, currentView, pendingLaunchIntent, selectedSchemaId]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const addToast = (type: 'success' | 'error' | 'info', message: string) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadInitialData = async () => {
    try {
      const schemasList = await api.getSchemas();
      setSchemas(schemasList);
      if (schemasList.length > 0) {
        if (!selectedSchemaId || !schemasList.some((s) => s.id === selectedSchemaId)) {
          setSelectedSchemaId(schemasList[0].id);
        }
      }
      await refreshHistory();
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const refreshHistory = async () => {
    try {
      const hist = await api.getHistory(50);
      setHistoryItems(hist);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const refreshSavedQueries = async () => {
    try {
      const saved = await api.getSavedQueries();
      setSavedQueries(saved);
    } catch (err) {
      console.error('Failed to fetch saved queries:', err);
    }
  };

  const handleDeleteHistoryItem = async (id: number) => {
    try {
      await api.deleteQuery(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
      addToast('info', 'Query removed from history.');
    } catch (err) {
      addToast('error', 'Failed to delete query record.');
    }
  };

  const handleDatasetUploaded = async (data: DatasetUploadResponse) => {
    const updatedSchemas = await api.getSchemas();
    setSchemas(updatedSchemas);
    setSelectedSchemaId(data.schema_id);
    setCurrentView('studio');
    addToast('success', `Switched to live uploaded dataset: ${data.schema_name}`);
  };

  const handleLaunchStudio = (schemaId?: number, initialPrompt?: string) => {
    if (!isAuthenticated) {
      setPendingLaunchIntent({ schemaId, initialPrompt });
      setCurrentView('auth');
      addToast('info', 'Please sign in with Google to access Query Studio.');
      return;
    }

    if (schemaId) setSelectedSchemaId(schemaId);
    if (initialPrompt) {
      setSelectedHistoricalQuery({
        id: 0,
        schema_id: schemaId || selectedSchemaId,
        natural_language_query: initialPrompt,
        generated_sql: '',
        confidence_score: 0.95,
        status: 'SUCCESS',
        execution_time_ms: 0,
        is_cached: false,
        created_at: new Date().toISOString(),
      });
    }
    setCurrentView('studio');
  };

  const handleOpenDatasetModal = () => {
    if (!isAuthenticated) {
      setCurrentView('auth');
      addToast('info', 'Please sign in with Google to upload custom datasets.');
      return;
    }
    setIsDatasetModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
      {/* Top Navbar */}
      <Navbar
        schemas={schemas}
        selectedSchemaId={selectedSchemaId}
        onSelectSchema={(id) => setSelectedSchemaId(id)}
        onOpenHistory={() => {
          refreshHistory();
          setIsHistoryOpen(true);
        }}
        onOpenSaved={() => {
          refreshSavedQueries();
          setIsSavedOpen(true);
        }}
        onOpenSchemaModal={handleOpenDatasetModal}
        onOpenDatasetModal={handleOpenDatasetModal}
        onOpenAuthModal={() => setCurrentView('auth')}
        currentView={currentView}
        onChangeView={(view) => {
          if (view === 'studio' && !isAuthenticated) {
            setCurrentView('auth');
            addToast('info', 'Please sign in with Google to access Query Studio.');
          } else if (view === 'admin' && !isAuthenticated) {
            setCurrentView('auth');
            addToast('info', 'Please sign in with an Administrator account.');
          } else {
            setCurrentView(view);
          }
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === 'home' ? (
          <HomePage
            schemas={schemas}
            onLaunchStudio={handleLaunchStudio}
            onOpenDatasetModal={handleOpenDatasetModal}
            onOpenAuthModal={() => setCurrentView('auth')}
          />
        ) : currentView === 'auth' ? (
          <GoogleAuthPage
            onSuccessToast={(msg) => addToast('success', msg)}
            onBackToHome={() => setCurrentView('home')}
            onExploreAsGuest={() => {
              handleLaunchStudio();
            }}
          />
        ) : currentView === 'studio' ? (
          <QueryStudio
            schemas={schemas}
            selectedSchemaId={selectedSchemaId}
            onRefreshSchemas={loadInitialData}
            onAddToast={addToast}
            onRefreshHistory={refreshHistory}
            selectedHistoricalQuery={selectedHistoricalQuery}
            onOpenDatasetModal={handleOpenDatasetModal}
          />
        ) : (
          <AdminDashboard />
        )}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/90 text-center text-xs text-slate-500 transition-colors">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© 2026 QueryCraft AI • Enterprise NLP to SQL Translation & Real-Time Data Ingestion</p>
          <div className="flex items-center gap-4 text-slate-400">
            <button onClick={() => setCurrentView('home')} className="hover:text-brand-600 dark:hover:text-brand-400">Home</button>
            <button onClick={() => setCurrentView('studio')} className="hover:text-brand-600 dark:hover:text-brand-400">Query Studio</button>
            <button onClick={() => setIsDatasetModalOpen(true)} className="hover:text-brand-600 dark:hover:text-brand-400">Upload Dataset</button>
          </div>
        </div>
      </footer>

      {/* Slide-out History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        historyItems={historyItems}
        onClose={() => setIsHistoryOpen(false)}
        onSelectQuery={(item) => {
          setSelectedHistoricalQuery(item);
          setCurrentView('studio');
        }}
        onDeleteHistoryItem={handleDeleteHistoryItem}
      />

      {/* Saved Queries Modal */}
      <SavedQueriesModal
        isOpen={isSavedOpen}
        savedQueries={savedQueries}
        onClose={() => setIsSavedOpen(false)}
        onSelectQuery={(nl, sql) => {
          setSelectedHistoricalQuery({
            id: 0,
            schema_id: selectedSchemaId,
            natural_language_query: nl,
            generated_sql: sql,
            confidence_score: 1.0,
            status: 'SUCCESS',
            execution_time_ms: 0,
            is_cached: false,
            created_at: new Date().toISOString(),
          });
          setCurrentView('studio');
        }}
      />

      {/* Real-time Dataset Upload Modal */}
      <DatasetUploadModal
        isOpen={isDatasetModalOpen}
        onClose={() => setIsDatasetModalOpen(false)}
        onDatasetUploaded={handleDatasetUploaded}
        onAddToast={addToast}
      />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccessToast={(msg) => addToast('success', msg)}
      />

      {/* Toast Notification Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onClose={removeToast} />
        ))}
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </ThemeProvider>
  );
}
