import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const ConnectionTest: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await apiService.checkHealth();
        if (response.success) {
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('error');
          setErrorMessage(response.error || 'Unknown error');
        }
      } catch (error) {
        setConnectionStatus('error');
        setErrorMessage(error instanceof Error ? error.message : 'Connection failed');
      }
    };

    testConnection();
  }, []);

  if (connectionStatus === 'checking') {
    return (
      <span className="hidden sm:inline-flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
        Checking…
      </span>
    );
  }

  if (connectionStatus === 'connected') {
    return (
      <span
        className="hidden sm:inline-flex items-center gap-1.5 text-xs text-teal-700 dark:text-teal-400"
        title="Backend connected"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
        Online
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400 max-w-[10rem] truncate"
      title={errorMessage || 'Backend connection failed'}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
      Offline
    </span>
  );
};

export default ConnectionTest;
