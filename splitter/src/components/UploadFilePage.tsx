import React from 'react';
import AppHeader from './AppHeader';
import FileUploader from './FileUploader';

interface UploadFilePageProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
  onBackClick: () => void;
  error?: string | null;
  selectedPaymentMode?: string;
}

const UploadFilePage: React.FC<UploadFilePageProps> = ({ 
  onFileSelect, 
  isProcessing, 
  onBackClick,
  error,
  selectedPaymentMode
}) => {
  return (
    <div className="w-full max-w-4xl mx-auto px-6">
      <AppHeader 
        title="Splitter"
        subtitle="Upload Your ATM Transaction File"
        showBackButton={true}
        onBackClick={onBackClick}
        backButtonText="← Back to Payment Mode Selection"
      />
      
      <div className="text-center mb-8">
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
          Selected payment mode: <span className="font-semibold text-blue-600 dark:text-blue-400">{selectedPaymentMode?.toUpperCase() || 'ATM Transactions'}</span>
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Upload your transaction file to extract ATM references, dates, and amounts
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400 dark:text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Processing Error</h3>
              <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <FileUploader onFileSelect={onFileSelect} isProcessing={isProcessing} />
    </div>
  );
};

export default UploadFilePage;
