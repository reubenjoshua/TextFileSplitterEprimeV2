import { useAppState } from './hooks/useAppState';
import SelectPaymentModePage from './components/SelectPaymentModePage';
import UploadFilePage from './components/UploadFilePage';
import ResultsPage from './components/ResultsPage';
import ConnectionTest from './components/ConnectionTest';
import ProgressBar from './components/ProgressBar';
import DarkModeToggle from './components/DarkModeToggle';
import StepIndicator from './components/StepIndicator';
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
    handleBackToUpload,
  } = useAppState();

  const renderCurrentPage = () => {
    switch (currentStep) {
      case 'select':
        return <SelectPaymentModePage onModeSelect={handlePaymentModeSelect} />;

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
      <div className="min-h-screen bg-slate-100 dark:bg-slate-950 transition-colors duration-300">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(15,118,110,0.06),_transparent_55%)] dark:bg-[radial-gradient(ellipse_at_top,_rgba(45,212,191,0.05),_transparent_50%)]" />

        <div className="relative">
          <header className="sticky top-0 z-40 border-b border-slate-200/80 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-8 h-8 bg-teal-700 dark:bg-teal-600 rounded-lg flex items-center justify-center shrink-0">
                  <span className="text-white text-sm font-bold">S</span>
                </div>
                <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">
                  Text File Splitter
                </span>
              </div>
              <div className="flex items-center gap-3">
                <ConnectionTest />
                <DarkModeToggle />
              </div>
            </div>
          </header>

          <main className="py-8 sm:py-10">
            <div className="px-4 sm:px-6 mb-2">
              <StepIndicator currentStep={currentStep} />
            </div>
            {renderCurrentPage()}
          </main>
        </div>

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
