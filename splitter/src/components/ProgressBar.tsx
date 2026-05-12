import React from 'react';

interface ProgressBarProps {
  progress: number;
  status: string;
  isVisible: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-md mx-4 shadow-xl">
        <div className="text-center">
          <div className="mb-4">
            <div className="w-12 h-12 mx-auto mb-4">
              <svg className="animate-spin h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Processing File</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{status}</p>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* Progress Percentage */}
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {progress}% Complete
          </div>
          
          {/* File size indicator */}
          {progress > 0 && progress < 100 && (
            <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
              Large file detected - this may take a moment
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
