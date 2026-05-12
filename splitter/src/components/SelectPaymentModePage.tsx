import React from 'react';
import AppHeader from './AppHeader';
import PaymentModeSelector from './PaymentModeSelector';

interface SelectPaymentModePageProps {
  onModeSelect: (modeId: string) => void;
}

const SelectPaymentModePage: React.FC<SelectPaymentModePageProps> = ({ onModeSelect }) => {
  return (
    <div className="w-full max-w-4xl mx-auto px-6">
      <AppHeader 
        title="Splitter"
        subtitle="Select Payment Mode"
      />
      
      <div className="text-center mb-8">
        <p className="text-gray-600 dark:text-gray-400">
          Choose how you want to process your transaction files
        </p>
      </div>
      
      <PaymentModeSelector onModeSelect={onModeSelect} />
    </div>
  );
};

export default SelectPaymentModePage;
