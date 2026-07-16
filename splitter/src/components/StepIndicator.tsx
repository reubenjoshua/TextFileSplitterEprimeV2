import React from 'react';
import type { AppStep } from '../types/Transaction';

interface StepIndicatorProps {
  currentStep: AppStep;
}

const steps: { id: AppStep; label: string; number: number }[] = [
  { id: 'select', label: 'Select Mode', number: 1 },
  { id: 'upload', label: 'Upload File', number: 2 },
  { id: 'results', label: 'Results', number: 3 },
];

const stepOrder: AppStep[] = ['select', 'upload', 'results'];

const StepIndicator: React.FC<StepIndicatorProps> = ({ currentStep }) => {
  const currentIndex = stepOrder.indexOf(currentStep);

  return (
    <nav aria-label="Progress" className="w-full max-w-lg mx-auto mb-8">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <React.Fragment key={step.id}>
              <li className="flex flex-col items-center gap-2">
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-all duration-300 ${
                    isComplete
                      ? 'bg-teal-700 text-white dark:bg-teal-500'
                      : isCurrent
                      ? 'bg-teal-700 text-white ring-4 ring-teal-100 dark:bg-teal-500 dark:ring-teal-900/40'
                      : 'bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-500'
                  }`}
                >
                  {isComplete ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={`text-xs font-medium ${
                    isCurrent || isComplete
                      ? 'text-teal-800 dark:text-teal-300'
                      : 'text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {step.label}
                </span>
              </li>

              {index < steps.length - 1 && (
                <li
                  className={`flex-1 h-0.5 mx-2 mb-6 rounded-full ${
                    index < currentIndex
                      ? 'bg-teal-600 dark:bg-teal-500'
                      : 'bg-slate-200 dark:bg-slate-800'
                  }`}
                  aria-hidden="true"
                />
              )}
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
};

export default StepIndicator;
