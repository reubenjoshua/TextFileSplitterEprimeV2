const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

export interface ProcessingResult {
  grouped_data: Record<string, any>;
  individual_transactions?: any[];
  raw_contents: string[];
  payment_mode: string;
  total_amount: number;
  total_transactions: number;
  original_filename?: string;
}

export interface ParserInfo {
  payment_mode: string;
  full_name: string;
  description: string;
  supported_formats: string[];
  file_format: {
    separator: string;
    minimum_fields: number;
    field_descriptions: string[];
  };
  extracted_fields: string[];
  validation_rules: string[];
  distinguishing_features: string[];
  date_format: {
    input: string;
    output: string;
    example: string;
  };
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  file_info?: any;
  requirements?: string[];
  common_errors?: string[];
}

class ApiService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // If not JSON, get text to see what we're getting
        const text = await response.text();
        console.error('Non-JSON response received:', text.substring(0, 200));
        return {
          success: false,
          error: `Server returned non-JSON response (${response.status}): ${response.statusText}`,
        };
      }

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  private async makeFileRequest<T>(
    endpoint: string,
    file: File,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Create AbortController for timeout handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes timeout

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // If not JSON, get text to see what we're getting
        const text = await response.text();
        console.error('Non-JSON response received:', text.substring(0, 200));
        return {
          success: false,
          error: `Server returned non-JSON response (${response.status}): ${response.statusText}`,
        };
      }

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      let errorMessage = 'Unknown error occurred';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Request timed out. Large files may take longer to process. Please try again.';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else {
          errorMessage = error.message;
        }
      }
      
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  // Health check
  async checkHealth(): Promise<ApiResponse<any>> {
    return this.makeRequest('/health');
  }

  // BDO endpoints
  async processBdoFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/bdo/process', file);
  }

  async getBdoInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/bdo/info');
  }

  async validateBdoFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/bdo/validate', file);
  }

  async getBdoSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/bdo/sample');
  }

  // Cebuana endpoints
  async processCebuanaFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/cebuana/process', file);
  }

  async getCebuanaInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/cebuana/info');
  }

  async validateCebuanaFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/cebuana/validate', file);
  }

  async getCebuanaSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/cebuana/sample');
  }

  async compareCebuanaWithEcpay(): Promise<ApiResponse<any>> {
    return this.makeRequest('/cebuana/compare');
  }

  // Chinabank endpoints
  async processChinabankFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/chinabank/process', file);
  }

  async getChinabankInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/chinabank/info');
  }

  async validateChinabankFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/chinabank/validate', file);
  }

  async getChinabankSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/chinabank/sample');
  }

  async compareChinabankWithOthers(): Promise<ApiResponse<any>> {
    return this.makeRequest('/chinabank/compare');
  }

  async getChinabankFormatGuide(): Promise<ApiResponse<any>> {
    return this.makeRequest('/chinabank/format-guide');
  }

  // ECPay endpoints
  async processEcpayFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/ecpay/process', file);
  }

  async getEcpayInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/ecpay/info');
  }

  async validateEcpayFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/ecpay/validate', file);
  }

  async getEcpaySample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/ecpay/sample');
  }

  async compareEcpayWithCebuana(file: File): Promise<ApiResponse<any>> {
    return this.makeFileRequest('/ecpay/compare', file);
  }

  async compareEcpayWithOthers(): Promise<ApiResponse<any>> {
    return this.makeRequest('/ecpay/compare');
  }

  async getEcpayFormatGuide(): Promise<ApiResponse<any>> {
    return this.makeRequest('/ecpay/format-guide');
  }

  // Metrobank endpoints
  async processMetrobankFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/metrobank/process', file);
  }

  async getMetrobankInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/metrobank/info');
  }

  async validateMetrobankFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/metrobank/validate', file);
  }

  async getMetrobankSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/metrobank/sample');
  }

  // Unionbank endpoints
  async processUnionbankFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/unionbank/process', file);
  }

  async getUnionbankInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/unionbank/info');
  }

  async validateUnionbankFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/unionbank/validate', file);
  }

  async getUnionbankSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/unionbank/sample');
  }

  // SM endpoints
  async processSmFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/sm/process', file);
  }

  async getSmInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/sm/info');
  }

  async validateSmFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/sm/validate', file);
  }

  async getSmSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/sm/sample');
  }

  // PNB endpoints
  async processPnbFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/pnb/process', file);
  }

  async getPnbInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/pnb/info');
  }

  async validatePnbFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/pnb/validate', file);
  }

  async getPnbSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/pnb/sample');
  }

  // CIS endpoints
  async processCisFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/cis/process', file);
  }

  async getCisInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/cis/info');
  }

  async validateCisFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/cis/validate', file);
  }

  async getCisSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/cis/sample');
  }

  // BANCNET endpoints
  async processBancnetFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/bancnet/process', file);
  }

  async getBancnetInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/bancnet/info');
  }

  async validateBancnetFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/bancnet/validate', file);
  }

  async getBancnetSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/bancnet/sample');
  }

  // ROBINSONS endpoints
  async processRobinsonsFile(file: File): Promise<ApiResponse<ProcessingResult>> {
    return this.makeFileRequest('/robinsons/process', file);
  }

  async getRobinsonsInfo(): Promise<ApiResponse<ParserInfo>> {
    return this.makeRequest('/robinsons/info');
  }

  async validateRobinsonsFile(file: File): Promise<ApiResponse<ValidationResult>> {
    return this.makeFileRequest('/robinsons/validate', file);
  }

  async getRobinsonsSample(): Promise<ApiResponse<any>> {
    return this.makeRequest('/robinsons/sample');
  }

  // Generic method for processing files based on payment mode
  async processFile(file: File, paymentMode: string): Promise<ApiResponse<ProcessingResult>> {
    switch (paymentMode.toLowerCase()) {
      case 'bdo':
        return this.processBdoFile(file);
      case 'cebuana':
        return this.processCebuanaFile(file);
      case 'chinabank':
        return this.processChinabankFile(file);
      case 'ecpay':
        return this.processEcpayFile(file);
      case 'metrobank':
        return this.processMetrobankFile(file);
      case 'unionbank':
        return this.processUnionbankFile(file);
      case 'sm':
        return this.processSmFile(file);
      case 'pnb':
        return this.processPnbFile(file);
      case 'cis':
        return this.processCisFile(file);
      case 'bancnet':
        return this.processBancnetFile(file);
      case 'robinsons':
        return this.processRobinsonsFile(file);
      default:
        return {
          success: false,
          error: `Unsupported payment mode: ${paymentMode}`,
        };
    }
  }

  // Generic method for validating files based on payment mode
  async validateFile(file: File, paymentMode: string): Promise<ApiResponse<ValidationResult>> {
    switch (paymentMode.toLowerCase()) {
      case 'bdo':
        return this.validateBdoFile(file);
      case 'cebuana':
        return this.validateCebuanaFile(file);
      case 'chinabank':
        return this.validateChinabankFile(file);
      case 'ecpay':
        return this.validateEcpayFile(file);
      case 'metrobank':
        return this.validateMetrobankFile(file);
      case 'unionbank':
        return this.validateUnionbankFile(file);
      case 'sm':
        return this.validateSmFile(file);
      case 'pnb':
        return this.validatePnbFile(file);
      case 'cis':
        return this.validateCisFile(file);
      case 'bancnet':
        return this.validateBancnetFile(file);
      case 'robinsons':
        return this.validateRobinsonsFile(file);
      default:
        return {
          success: false,
          error: `Unsupported payment mode: ${paymentMode}`,
        };
    }
  }

  // Generic method for getting parser info based on payment mode
  async getParserInfo(paymentMode: string): Promise<ApiResponse<ParserInfo>> {
    switch (paymentMode.toLowerCase()) {
      case 'bdo':
        return this.getBdoInfo();
      case 'cebuana':
        return this.getCebuanaInfo();
      case 'chinabank':
        return this.getChinabankInfo();
      case 'ecpay':
        return this.getEcpayInfo();
      case 'metrobank':
        return this.getMetrobankInfo();
      case 'unionbank':
        return this.getUnionbankInfo();
      case 'sm':
        return this.getSmInfo();
      case 'pnb':
        return this.getPnbInfo();
      case 'cis':
        return this.getCisInfo();
      case 'bancnet':
        return this.getBancnetInfo();
      case 'robinsons':
        return this.getRobinsonsInfo();
      default:
        return {
          success: false,
          error: `Unsupported payment mode: ${paymentMode}`,
        };
    }
  }

  // Export functions
  async exportCsv(transactions: any[], paymentMode: string, originalFilename?: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/export/csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transactions,
          payment_mode: paymentMode,
          original_filename: originalFilename
        })
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('CSV export error:', error);
      return null;
    }
  }

  async exportJson(transactions: any[], paymentMode: string, originalFilename?: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/export/json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transactions,
          payment_mode: paymentMode,
          original_filename: originalFilename
        })
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('JSON export error:', error);
      return null;
    }
  }

  async generateComprehensiveReport(
    processedData: any, 
    rawContents: string[], 
    originalFilename: string, 
    paymentMode: string,
    detectedHeader?: string
  ): Promise<Blob | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/export/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          processed_data: processedData,
          raw_contents: rawContents,
          original_filename: originalFilename,
          payment_mode: paymentMode,
          detected_header: detectedHeader
        })
      });

      if (!response.ok) {
        throw new Error(`Report generation failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Comprehensive report generation error:', error);
      return null;
    }
  }
}

export const apiService = new ApiService();
