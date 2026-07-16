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
  backButtonText = 'Back',
  additionalButtons = [],
}) => {
  const getButtonStyles = (variant: 'primary' | 'secondary' = 'secondary') => {
    const base =
      'inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900';
    if (variant === 'primary') {
      return `${base} bg-teal-700 text-white hover:bg-teal-800 focus:ring-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500`;
    }
    return `${base} bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 focus:ring-slate-400 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-700`;
  };

  return (
    <div className="mb-8">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
              {subtitle}
            </p>
          )}
        </div>

        {(showBackButton && onBackClick) || additionalButtons.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {showBackButton && onBackClick && (
              <button onClick={onBackClick} className={getButtonStyles('secondary')}>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
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
    </div>
  );
};

export default AppHeader;
