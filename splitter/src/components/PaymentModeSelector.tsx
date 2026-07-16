import React, { useMemo, useState } from 'react';

interface PaymentMode {
  id: string;
  name: string;
  description: string;
  badge?: string;
}

const paymentModes: PaymentMode[] = [
  { id: 'bdo', name: 'BDO', description: 'Pipe-separated BDO transactions' },
  { id: 'cebuana', name: 'CEBUANA', description: 'Comma-separated Cebuana files' },
  { id: 'chinabank', name: 'CHINABANK', description: 'China Bank transaction files' },
  { id: 'ecpay', name: 'ECPAY', description: 'ECPay with PAY&GO support', badge: 'EPR / PIC' },
  { id: 'metrobank', name: 'METROBANK', description: 'Space-separated Metrobank files' },
  { id: 'unionbank', name: 'UNIONBANK', description: 'UnionBank transaction files' },
  { id: 'sm', name: 'SM', description: 'SM payment files with headers' },
  { id: 'pnb', name: 'PNB', description: 'PNB caret-separated files' },
  { id: 'cis', name: 'CIS', description: 'CIS Bayad caret-separated', badge: 'RTP' },
  { id: 'bancnet', name: 'BANCNET', description: 'BancNet transaction files' },
  { id: 'robinsons', name: 'ROBINSONS', description: 'Robinsons payment files' },
];

interface PaymentModeSelectorProps {
  onModeSelect: (modeId: string) => void;
}

const PaymentModeSelector: React.FC<PaymentModeSelectorProps> = ({ onModeSelect }) => {
  const [search, setSearch] = useState('');
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const filteredModes = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return paymentModes;
    return paymentModes.filter(
      (mode) =>
        mode.name.toLowerCase().includes(query) ||
        mode.description.toLowerCase().includes(query) ||
        (mode.badge && mode.badge.toLowerCase().includes(query))
    );
  }, [search]);

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-6">
        <label htmlFor="mode-search" className="sr-only">
          Search payment modes
        </label>
        <div className="relative">
          <svg
            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            id="mode-search"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search payment modes..."
            className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent shadow-sm"
          />
        </div>
      </div>

      {filteredModes.length === 0 ? (
        <div className="panel p-10 text-center">
          <p className="text-slate-600 dark:text-slate-400">No payment modes match “{search}”.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredModes.map((mode) => {
            const isHovered = hoveredId === mode.id;
            return (
              <button
                key={mode.id}
                type="button"
                onClick={() => onModeSelect(mode.id)}
                onMouseEnter={() => setHoveredId(mode.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`group text-left p-4 rounded-xl border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2 dark:focus:ring-offset-slate-950 ${
                  isHovered
                    ? 'border-teal-500 bg-teal-50/80 dark:bg-teal-950/40 dark:border-teal-500 shadow-md -translate-y-0.5'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-teal-400 dark:hover:border-teal-600'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
                    {mode.name}
                  </span>
                  {mode.badge && (
                    <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-md bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-300">
                      {mode.badge}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-snug">
                  {mode.description}
                </p>
                <div
                  className={`mt-3 text-xs font-medium transition-opacity duration-200 ${
                    isHovered ? 'opacity-100 text-teal-700 dark:text-teal-400' : 'opacity-0'
                  }`}
                >
                  Continue →
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PaymentModeSelector;
