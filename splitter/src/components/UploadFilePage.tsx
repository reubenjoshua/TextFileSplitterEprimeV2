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
  selectedPaymentMode,
}) => {
  return (
    <div className="w-full max-w-3xl mx-auto px-4 sm:px-6">
      <AppHeader
        title="Upload file"
        subtitle="Drop a TXT, CSV, or LOG file to extract and group transactions"
        showBackButton={true}
        onBackClick={onBackClick}
        backButtonText="Change mode"
      />

      <div className="panel p-6 sm:p-8 mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <span className="text-sm text-slate-500 dark:text-slate-400">Selected mode</span>
          <span className="inline-flex items-center px-3 py-1 rounded-lg text-sm font-semibold bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-200">
            {selectedPaymentMode?.toUpperCase() || '—'}
          </span>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900">
            <div className="flex gap-3">
              <div className="shrink-0 mt-0.5">
                <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">
                  Couldn’t process this file
                </h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        <FileUploader onFileSelect={onFileSelect} isProcessing={isProcessing} />
      </div>

      <div className="text-center text-xs text-slate-400 dark:text-slate-500">
        Tip: For CIS, include RTP/NONRTP in the filename. For ECPAY, use ePRIME or PRIMEWATER.
      </div>
    </div>
  );
};

export default UploadFilePage;
