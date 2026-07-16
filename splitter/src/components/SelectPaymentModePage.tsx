import React from 'react';
import AppHeader from './AppHeader';
import PaymentModeSelector from './PaymentModeSelector';

interface SelectPaymentModePageProps {
  onModeSelect: (modeId: string) => void;
}

const SelectPaymentModePage: React.FC<SelectPaymentModePageProps> = ({ onModeSelect }) => {
  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6">
      <AppHeader
        title="Select payment mode"
        subtitle="Choose the bank or channel that matches your transaction file"
      />

      <PaymentModeSelector onModeSelect={onModeSelect} />
    </div>
  );
};

export default SelectPaymentModePage;
