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

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'checking':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'connected':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'checking':
        return (
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
      case 'connected':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'checking':
        return 'Checking backend connection...';
      case 'connected':
        return 'Backend connected successfully!';
      case 'error':
        return 'Backend connection failed';
    }
  };

  // Only show the connection status if there's an error
  if (connectionStatus === 'error') {
    return (
      <div className={`fixed top-4 right-4 p-3 rounded-lg border ${getStatusColor()} shadow-lg z-50`}>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <div>
            <p className="font-medium text-sm">{getStatusText()}</p>
            <p className="text-xs mt-1">{errorMessage}</p>
          </div>
        </div>
      </div>
    );
  }

  // Hide the success and checking messages
  return null;
};

export default ConnectionTest;
