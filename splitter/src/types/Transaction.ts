export interface TransactionData {
  atmRef?: string;
  date?: string;
  amount?: string;
  type?: string;
  account?: string;
  rawText: string;
  transactionCount?: number;
  paymentMode?: string;
}

export type AppStep = 'select' | 'upload' | 'results';
