import React, { useRef, useState } from 'react';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ onFileSelect, isProcessing }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-2xl p-10 sm:p-12 text-center transition-all duration-200 ${
          dragActive
            ? 'border-teal-500 bg-teal-50 dark:border-teal-400 dark:bg-teal-950/30 scale-[1.01]'
            : 'border-slate-300 dark:border-slate-600 hover:border-teal-400 dark:hover:border-teal-500 hover:bg-slate-50/80 dark:hover:bg-slate-800/40'
        } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!isProcessing ? handleClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.csv,.log"
          onChange={handleFileChange}
          className="hidden"
          disabled={isProcessing}
        />

        {isProcessing ? (
          <div className="space-y-4">
            <div className="animate-spin w-12 h-12 border-4 border-teal-200 border-t-teal-700 rounded-full mx-auto" />
            <p className="text-slate-600 dark:text-slate-300 font-medium">Processing your file…</p>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="w-16 h-16 mx-auto bg-teal-100 dark:bg-teal-900/40 rounded-2xl flex items-center justify-center">
              <svg
                className="w-8 h-8 text-teal-700 dark:text-teal-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            <div>
              <p className="text-lg font-semibold text-slate-900 dark:text-white mb-1">
                Drop your file here
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                or click to browse · TXT, CSV, LOG
              </p>
            </div>

            <div className="flex justify-center">
              <span className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-white bg-teal-700 hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-500 transition-colors duration-200 shadow-sm">
                Choose file
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploader;
