import React from 'react';
import { apiService } from '../services/api';

interface TransactionData {
  atmRef?: string;
  date?: string;
  amount?: string;
  type?: string;
  account?: string;
  rawText: string;
}

interface ProcessingResultsProps {
  results: TransactionData[];
  paymentMode: string;
  isLoading: boolean;
  totalAmount?: number;
}

const ProcessingResults: React.FC<ProcessingResultsProps> = ({
  results,
  paymentMode,
  isLoading,
  totalAmount,
}) => {
  const [isExporting, setIsExporting] = React.useState(false);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [itemsPerPage, setItemsPerPage] = React.useState(10);

  const totalPages = Math.ceil(results.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentResults = results.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const startPage = Math.max(1, currentPage - 2);
      const endPage = Math.min(totalPages, currentPage + 2);

      if (startPage > 1) {
        pages.push(1);
        if (startPage > 2) {
          pages.push('...');
        }
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }

      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push('...');
        }
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      const processingResult = (window as any).lastProcessingResult;
      const originalFilename = processingResult?.original_filename || 'transactions';

      if (!processingResult) {
        const blob = await apiService.exportCsv(results, paymentMode, originalFilename);
        if (blob) {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          const baseFilename = originalFilename.replace(/\.[^/.]+$/, '');
          link.download = `${baseFilename}.csv`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }
        return;
      }

      const blob = await apiService.generateComprehensiveReport(
        processingResult.grouped_data,
        processingResult.raw_contents,
        originalFilename,
        paymentMode,
        processingResult.detected_header,
        processingResult.rtp_type,
        processingResult.product_suffix
      );

      if (blob) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const baseFilename = originalFilename.replace(/\.[^/.]+$/, '');
        link.download = `${baseFilename}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const formatAmount = (amount: string | undefined) => {
    if (!amount) return 'N/A';
    const num = parseFloat(amount.replace(/[^0-9.-]/g, ''));
    return isNaN(num) ? amount : `₱${num.toLocaleString()}`;
  };

  const formatDate = (date: string | undefined) => {
    if (!date) return 'N/A';
    try {
      const parsedDate = new Date(date);
      return parsedDate.toLocaleDateString();
    } catch {
      return date;
    }
  };

  const modeLabel = paymentMode.toUpperCase();
  const processingResult = (window as any).lastProcessingResult;
  const detectedTags: string[] = [];
  if (processingResult?.rtp_type) detectedTags.push(processingResult.rtp_type);
  if (processingResult?.product_suffix) detectedTags.push(processingResult.product_suffix);

  if (isLoading) {
    return (
      <div className="panel p-10 text-center">
        <div className="animate-spin w-12 h-12 border-4 border-teal-200 border-t-teal-700 rounded-full mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Processing results</h3>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Analyzing your transaction data…</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="panel p-10 text-center">
        <div className="w-14 h-14 mx-auto bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-4">
          <svg className="w-7 h-7 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.75}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">No results yet</h3>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Upload a file to see parsed transactions here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="panel p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500 mb-1">
            Transactions
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white tabular-nums">
            {results.length.toLocaleString()}
          </p>
        </div>
        <div className="panel p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500 mb-1">
            Total amount
          </p>
          <p className="text-2xl font-bold text-teal-700 dark:text-teal-400 tabular-nums">
            {totalAmount !== undefined
              ? `₱${totalAmount.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
              : '—'}
          </p>
        </div>
      </div>

      {/* Action bar */}
      <div className="panel p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Ready to download</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {modeLabel}
            </span>
            {detectedTags.map((tag) => (
              <span
                key={tag}
                className="text-xs font-semibold px-2 py-0.5 rounded-md bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-300"
              >
                {tag}
              </span>
            ))}
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Download the ZIP with split ATM files and summary CSV.
          </p>
        </div>
        <button
          onClick={handleExportCsv}
          disabled={isExporting}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-500 text-white text-sm font-semibold rounded-lg shadow-sm disabled:opacity-60 disabled:cursor-not-allowed transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          {isExporting ? 'Generating…' : 'Download split report'}
        </button>
      </div>

      {/* Table */}
      <div className="panel overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800">
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Transaction preview</h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 dark:bg-slate-800/80">
              <tr>
                {['ATM Ref', 'Date', 'Amount', 'Type', 'Account', 'Raw Text'].map((header) => (
                  <th
                    key={header}
                    className="px-5 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {currentResults.map((transaction, index) => (
                <tr
                  key={index}
                  className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors duration-100"
                >
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="text-sm font-mono font-medium text-slate-900 dark:text-slate-100">
                      {transaction.atmRef || 'N/A'}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap text-sm text-slate-700 dark:text-slate-300">
                    {formatDate(transaction.date)}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="text-sm font-semibold text-teal-700 dark:text-teal-400">
                      {formatAmount(transaction.amount)}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className="inline-flex px-2 py-0.5 text-xs font-medium rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {transaction.type || 'Transaction'}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400">
                    {transaction.account || 'N/A'}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-mono max-w-xs truncate block">
                      {transaction.rawText}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="px-5 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-500 dark:text-slate-400">Show</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
                    className="px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                  >
                    {[10, 25, 50, 100, 200].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                  <span className="text-sm text-slate-500 dark:text-slate-400">per page</span>
                </div>
                <div className="text-sm text-slate-500 dark:text-slate-400">
                  {startIndex + 1}–{Math.min(endIndex, results.length)} of {results.length}
                </div>
              </div>

              <div className="flex items-center justify-center gap-1.5 flex-wrap">
                <button
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1}
                  className="px-2.5 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200"
                  title="First page"
                >
                  ««
                </button>
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200"
                >
                  Previous
                </button>

                {getPageNumbers().map((page, index) =>
                  page === '...' ? (
                    <span key={index} className="px-2 text-sm text-slate-400">
                      …
                    </span>
                  ) : (
                    <button
                      key={index}
                      onClick={() => handlePageChange(page as number)}
                      className={`min-w-[2.25rem] px-2.5 py-1.5 text-sm rounded-lg border transition-colors ${
                        currentPage === page
                          ? 'bg-teal-700 dark:bg-teal-600 text-white border-teal-700 dark:border-teal-600'
                          : 'border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      {page}
                    </button>
                  )
                )}

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200"
                >
                  Next
                </button>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages}
                  className="px-2.5 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200"
                  title="Last page"
                >
                  »»
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingResults;
