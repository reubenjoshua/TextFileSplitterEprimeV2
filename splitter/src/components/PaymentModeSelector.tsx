import React, { useState } from 'react';

interface PaymentMode {
  id: string;
  name: string;
}

const paymentModes: PaymentMode[] = [
  { id: '', name: 'Select a payment mode' },
  { id: 'bdo', name: 'BDO' },
  { id: 'cebuana', name: 'CEBUANA' },
  { id: 'chinabank', name: 'CHINABANK' },
  { id: 'ecpay', name: 'ECPAY' },
  { id: 'metrobank', name: 'METROBANK' },
  { id: 'unionbank', name: 'UNIONBANK' },
  { id: 'sm', name: 'SM' },
  { id: 'pnb', name: 'PNB' },
  { id: 'cis', name: 'CIS' },
  { id: 'bancnet', name: 'BANCNET' },
  { id: 'robinsons', name: 'ROBINSONS' }
];

interface PaymentModeSelectorProps {
  onModeSelect: (modeId: string) => void;
}

const PaymentModeSelector: React.FC<PaymentModeSelectorProps> = ({ onModeSelect }) => {
  const [selectedMode, setSelectedMode] = useState<string>('');
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const handleModeSelect = (modeId: string, modeName: string) => {
    if (modeId === '') return; // Don't select the placeholder
    
    setSelectedMode(modeName);
    setIsOpen(false);
    onModeSelect(modeId);
  };

  const selectedModeData = paymentModes.find(m => m.name === selectedMode);

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Payment Mode:
        </label>
        
        <div className="relative">
          <button
            type="button"
            className="relative w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm pl-3 pr-10 py-3 text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-400 dark:hover:border-gray-500 transition-colors duration-200"
            onClick={() => setIsOpen(!isOpen)}
          >
            <span className={`block truncate ${selectedMode ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>
              {selectedMode || 'Select a payment mode'}
            </span>
            <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <svg
                className={`w-5 h-5 text-gray-400 transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          </button>

          {isOpen && (
            <div className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-700 shadow-lg max-h-60 rounded-lg py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none border border-gray-200 dark:border-gray-600">
              {paymentModes.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  className={`w-full text-left px-4 py-2 text-sm cursor-pointer transition-colors duration-150 ${
                    mode.id === ''
                      ? 'text-gray-400 dark:text-gray-500 cursor-default'
                      : selectedMode === mode.name
                      ? 'bg-blue-50 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
                      : 'text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                  onClick={() => handleModeSelect(mode.id, mode.name)}
                  disabled={mode.id === ''}
                >
                  {mode.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {selectedMode && selectedModeData && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center px-4 py-2 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-lg text-sm font-medium">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              {selectedModeData.name} selected
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentModeSelector;
