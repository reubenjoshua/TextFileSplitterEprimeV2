import React from 'react';

interface ActionButton {
  text: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

interface AppHeaderProps {
  title: string;
  subtitle?: string;
  showBackButton?: boolean;
  onBackClick?: () => void;
  backButtonText?: string;
  additionalButtons?: ActionButton[];
}

const AppHeader: React.FC<AppHeaderProps> = ({ 
  title, 
  subtitle, 
  showBackButton = false, 
  onBackClick, 
  backButtonText = "← Back",
  additionalButtons = []
}) => {
  const getButtonStyles = (variant: 'primary' | 'secondary' = 'secondary') => {
    const baseStyles = "px-6 py-2 text-sm font-medium rounded-lg transition-colors duration-200";
    if (variant === 'primary') {
      return `${baseStyles} bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600`;
    }
    return `${baseStyles} text-gray-600 hover:text-gray-900 border border-gray-300 hover:bg-gray-50 dark:text-gray-300 dark:hover:text-white dark:border-gray-600 dark:hover:bg-gray-700`;
  };

  return (
    <div className="text-center mb-8">
      <div className="flex items-center justify-center space-x-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
          <span className="text-white font-bold text-xl">S</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">{title}</h1>
      </div>
      
      {subtitle && (
        <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
          {subtitle}
        </h2>
      )}
      
      {(showBackButton && onBackClick) || additionalButtons.length > 0 ? (
        <div className="flex items-center justify-center space-x-3">
          {showBackButton && onBackClick && (
            <button
              onClick={onBackClick}
              className={getButtonStyles('secondary')}
            >
              {backButtonText}
            </button>
          )}
          
          {additionalButtons.map((button, index) => (
            <button
              key={index}
              onClick={button.onClick}
              className={getButtonStyles(button.variant)}
            >
              {button.text}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default AppHeader;
