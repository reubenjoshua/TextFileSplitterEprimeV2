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
  totalAmount 
}) => {
  return (
    <div className="w-full max-w-6xl mx-auto px-6">
      <AppHeader 
        title="Splitter"
        showBackButton={true}
        onBackClick={onBackClick}
        backButtonText="← Process Another File"
        additionalButtons={[
          {
            text: "📁 Back to Choose Files",
            onClick: onBackToUpload,
            variant: 'primary'
          }
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
