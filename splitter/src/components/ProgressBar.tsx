import React from 'react';

interface ProgressBarProps {
  progress: number;
  status: string;
  isVisible: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 w-full max-w-sm shadow-xl border border-slate-200 dark:border-slate-800">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4">
            <svg className="animate-spin h-12 w-12 text-teal-700 dark:text-teal-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">Processing file</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">{status}</p>

          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 mb-3 overflow-hidden">
            <div
              className="bg-teal-700 dark:bg-teal-500 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="text-sm font-medium text-slate-600 dark:text-slate-300 tabular-nums">
            {progress}% complete
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
