import { useState } from 'react';
import type { TransactionData, AppStep } from '../types/Transaction';
import { apiService } from '../services/api';
import type { ProcessingResult } from '../services/api';

export const useAppState = () => {
  const [selectedPaymentMode, setSelectedPaymentMode] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [results, setResults] = useState<TransactionData[]>([]);
  const [currentStep, setCurrentStep] = useState<AppStep>('select');
  const [error, setError] = useState<string | null>(null);
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);
  const [processingProgress, setProcessingProgress] = useState<number>(0);
  const [processingStatus, setProcessingStatus] = useState<string>('');

  const handlePaymentModeSelect = (modeId: string) => {
    setSelectedPaymentMode(modeId);
    setCurrentStep('upload');
  };

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setIsProcessing(true);
    setError(null);
    setProcessingResult(null);
    setProcessingProgress(0);
    setProcessingStatus('Starting file processing...');
    
    try {
      // Simulate progress for large files
      const fileSize = file.size;
      const isLargeFile = fileSize > 100000; // 100KB threshold
      
      if (isLargeFile) {
        // Simulate progress steps for large files
        const progressSteps = [
          { progress: 10, status: 'Reading file...' },
          { progress: 25, status: 'Validating format...' },
          { progress: 40, status: 'Parsing transactions...' },
          { progress: 60, status: 'Grouping by ATM reference...' },
          { progress: 80, status: 'Calculating totals...' },
          { progress: 95, status: 'Finalizing results...' }
        ];
        
        // Simulate progress updates
        for (const step of progressSteps) {
          await new Promise(resolve => setTimeout(resolve, 200));
          setProcessingProgress(step.progress);
          setProcessingStatus(step.status);
        }
      } else {
        setProcessingStatus('Processing file...');
        setProcessingProgress(50);
      }
      
      // Call the real API based on selected payment mode
      const response = await apiService.processFile(file, selectedPaymentMode);
      
              if (response.success && response.data) {
                setProcessingResult(response.data);
                
                // Store processing result globally for report generation
                (window as any).lastProcessingResult = response.data;

                // Convert individual transactions from backend (like old splitter)
                const convertedResults: TransactionData[] = [];
        
        // Use individual_transactions if available (preferred)
        if (response.data.individual_transactions && Array.isArray(response.data.individual_transactions)) {
          response.data.individual_transactions.forEach((transaction: any) => {
            convertedResults.push({
              atmRef: transaction.atm_ref || 'N/A',
              date: transaction.date || 'N/A',
              amount: transaction.amount?.toString() || '0',
              type: 'ATM Transaction',
              account: 'N/A',
              rawText: transaction.raw_text || '',
              transactionCount: 1,
              paymentMode: transaction.payment_mode || selectedPaymentMode
            });
          });
        } else {
          // Fallback: convert grouped data to individual transactions
          if (response.data.grouped_data && typeof response.data.grouped_data === 'object') {
            Object.entries(response.data.grouped_data).forEach(([atmRef, group]: [string, any]) => {
            if (group && group.raw_contents && Array.isArray(group.raw_contents)) {
              group.raw_contents.forEach((rawLine: string, index: number) => {
                const dates = Array.isArray(group.dates) ? group.dates : [];
                const date = dates[index] || dates[0] || 'N/A';
                
                // Add null checks for total_amount and transaction_count
                const totalAmount = group.total_amount || 0;
                const transactionCount = group.transaction_count || 1;
                const amount = transactionCount > 0 ? (parseFloat(totalAmount) / transactionCount).toString() : '0';
                
                convertedResults.push({
                  atmRef: atmRef,
                  date: date,
                  amount: amount,
                  type: 'ATM Transaction',
                  account: 'N/A',
                  rawText: rawLine,
                  transactionCount: 1,
                  paymentMode: group.payment_mode || selectedPaymentMode
                });
              });
            }
          });
          }
        }
        
        setResults(convertedResults);
        setProcessingProgress(100);
        setProcessingStatus('Processing complete!');
        setCurrentStep('results');
      } else {
        setError(response.error || 'Failed to process file');
        setCurrentStep('upload'); // Stay on upload page to show error
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setCurrentStep('upload'); // Stay on upload page to show error
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setSelectedPaymentMode('');
    setSelectedFile(null);
    setIsProcessing(false);
    setResults([]);
    setCurrentStep('select');
    setError(null);
    setProcessingResult(null);
    setProcessingProgress(0);
    setProcessingStatus('');
  };

  const handleBackToUpload = () => {
    setSelectedFile(null);
    setResults([]);
    setCurrentStep('upload');
    setError(null);
    setProcessingResult(null);
    setProcessingProgress(0);
    setProcessingStatus('');
  };

  return {
    selectedPaymentMode,
    selectedFile,
    isProcessing,
    results,
    currentStep,
    error,
    processingResult,
    processingProgress,
    processingStatus,
    handlePaymentModeSelect,
    handleFileSelect,
    handleReset,
    handleBackToUpload
  };
};
