from abc import ABC, abstractmethod
from typing import List, Dict, Any
import re
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """Base class for all payment mode parsers"""
    
    def __init__(self, payment_mode: str):
        self.payment_mode = payment_mode
        self.transactions = []
    
    @abstractmethod
    def parse_file(self, file_content: str) -> List[Dict[str, Any]]:
        """
        Parse the uploaded file content and extract transaction data
        
        Args:
            file_content (str): The content of the uploaded file
            
        Returns:
            List[Dict[str, Any]]: List of parsed transactions
        """
        pass
    
    def extract_amount(self, text: str) -> str:
        """Extract amount from text using regex patterns"""
        # Common amount patterns
        patterns = [
            r'[\$₱]\s*([\d,]+\.?\d*)',  # $100.00 or ₱100.00
            r'Amount[:\s]*([\d,]+\.?\d*)',  # Amount: 100.00
            r'(\d{1,3}(?:,\d{3})*\.?\d*)',  # 1,000.00 or 1000.00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'N/A'
    
    def extract_date(self, text: str) -> str:
        """Extract date from text using regex patterns"""
        # Common date patterns
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4})',  # DD Mon YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'N/A'
    
    def extract_reference(self, text: str, patterns: List[str]) -> str:
        """Extract reference number using provided patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return 'N/A'
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        return re.sub(r'\s+', ' ', text.strip())
    
    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Validate if transaction has required fields"""
        required_fields = ['rawText']
        return all(field in transaction and transaction[field] for field in required_fields)
    
    def format_response(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the response with metadata"""
        return {
            'payment_mode': self.payment_mode,
            'total_transactions': len(transactions),
            'processed_at': datetime.now().isoformat(),
            'transactions': transactions
        }
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches the expected format for this payment mode"""
        lines = file_content.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            if not line.strip():
                continue
                
            if self._is_valid_line(line):
                return True
                
        return False
    
    @abstractmethod
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches the expected format for this payment mode"""
        pass
