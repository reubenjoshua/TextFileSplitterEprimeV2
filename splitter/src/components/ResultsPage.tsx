import React from 'react';
import AppHeader from './AppHeader';
import ProcessingResults from './ProcessingResults';
import type { TransactionData } from '../types/Transaction';

interface ResultsPageProps {
  results: TransactionData[];
  isProcessing: boolean;
  onBackClick: () => void;
  onBackToUpload: () => void;
  selectedPaymentMode?: string;
  totalAmount?: number;
}

const ResultsPage: React.FC<ResultsPageProps> = ({
  results,
  isProcessing,
  onBackClick,
  onBackToUpload,
  selectedPaymentMode,
  totalAmount,
}) => {
  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-6">
      <AppHeader
        title="Results"
        subtitle="Review transactions and download your split report"
        showBackButton={true}
        onBackClick={onBackClick}
        backButtonText="Start over"
        additionalButtons={[
          {
            text: 'Upload another',
            onClick: onBackToUpload,
            variant: 'primary',
          },
        ]}
      />

      <ProcessingResults
        results={results}
        paymentMode={selectedPaymentMode || 'ATM Transactions'}
        isLoading={isProcessing}
        totalAmount={totalAmount}
      />
    </div>
  );
};

export default ResultsPage;
