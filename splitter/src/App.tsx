import { useAppState } from './hooks/useAppState';
import SelectPaymentModePage from './components/SelectPaymentModePage';
import UploadFilePage from './components/UploadFilePage';
import ResultsPage from './components/ResultsPage';
import ConnectionTest from './components/ConnectionTest';
import ProgressBar from './components/ProgressBar';
import DarkModeToggle from './components/DarkModeToggle';
import { DarkModeProvider } from './contexts/DarkModeContext';

function App() {
  const {
    isProcessing,
    results,
    currentStep,
    error,
    selectedPaymentMode,
    processingResult,
    processingProgress,
    processingStatus,
    handlePaymentModeSelect,
    handleFileSelect,
    handleReset,
    handleBackToUpload
  } = useAppState();

  const renderCurrentPage = () => {
    switch (currentStep) {
      case 'select':
        return (
          <SelectPaymentModePage 
            onModeSelect={handlePaymentModeSelect} 
          />
        );
      
      case 'upload':
        return (
          <UploadFilePage
            onFileSelect={handleFileSelect}
            isProcessing={isProcessing}
            onBackClick={handleReset}
            error={error}
            selectedPaymentMode={selectedPaymentMode}
          />
        );
      
      case 'results':
        return (
          <ResultsPage 
            results={results}
            isProcessing={isProcessing}
            onBackClick={handleReset}
            onBackToUpload={handleBackToUpload}
            selectedPaymentMode={selectedPaymentMode}
            totalAmount={processingResult?.total_amount}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <DarkModeProvider>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-300">
        <DarkModeToggle />
        <ConnectionTest />
        <main className="py-8">
          {renderCurrentPage()}
        </main>
        
        {/* Progress Bar Overlay */}
        <ProgressBar 
          progress={processingProgress}
          status={processingStatus}
          isVisible={isProcessing}
        />
      </div>
    </DarkModeProvider>
  );
}

export default App;
