import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class CISParser(BaseParser):
    """Parser for CIS (CIS Bayad) transaction files"""
    
    def __init__(self):
        super().__init__("CIS")
        self.separator = '^'
        self.min_fields = 3
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse CIS transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing CIS file with {len(lines)} lines")
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                raw_contents.append(line)
                
                # For CIS, split by caret
                fields = [f.strip() for f in line.split('^')]
                
                # Validate minimum fields
                if len(fields) < self.min_fields:
                    logger.warning(f"CIS line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                    continue
                
                # Parse the transaction line
                transaction = self._parse_transaction_line(line, fields, line_num)
                if transaction:
                    atm_ref = transaction['atm_ref']
                    
                    # Initialize group if not exists
                    if atm_ref not in grouped_data:
                        grouped_data[atm_ref] = {
                            'raw_contents': [],
                            'transaction_count': 0,
                            'total_amount': 0.0,
                            'payment_mode': self.payment_mode,
                            'dates': set(),
                            'transactions': [],
                            'atm_refs': set()
                        }
                    
                    # Add to group
                    grouped_data[atm_ref]['raw_contents'].append(line)
                    grouped_data[atm_ref]['transaction_count'] += 1
                    grouped_data[atm_ref]['total_amount'] += transaction['amount']
                    grouped_data[atm_ref]['dates'].add(transaction['date'])
                    grouped_data[atm_ref]['transactions'].append(transaction)
                    grouped_data[atm_ref]['atm_refs'].add(transaction['full_atm_ref'])
                    
                    total_amount += transaction['amount']
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                if 'dates' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['dates'], set):
                    grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
                if 'atm_refs' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['atm_refs'], set):
                    grouped_data[atm_ref]['atm_refs'] = list(grouped_data[atm_ref]['atm_refs'])
            
            logger.info(f"CIS processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
            # Create individual transactions list for frontend compatibility
            individual_transactions = []
            for atm_ref, group in grouped_data.items():
                if group.get('transactions'):
                    individual_transactions.extend(group['transactions'])
                else:
                    # Create individual transactions from raw contents if detailed transactions not available
                    for i, raw_line in enumerate(group['raw_contents']):
                        dates = group['dates'] if isinstance(group['dates'], list) else []
                        date = dates[i] if i < len(dates) else (dates[0] if dates else 'N/A')
                        amount = group['total_amount'] / group['transaction_count'] if group['transaction_count'] > 0 else 0
                        
                        individual_transactions.append({
                            'atm_ref': atm_ref,
                            'date': date,
                            'amount': amount,
                            'raw_text': raw_line,
                            'payment_mode': self.payment_mode
                        })
            
            return {
                'grouped_data': grouped_data,
                'individual_transactions': individual_transactions,
                'raw_contents': raw_contents,
                'payment_mode': self.payment_mode,
                'total_amount': total_amount,
                'total_transactions': len([line for line in raw_contents if line.strip()]),
            }
            
        except Exception as e:
            logger.error(f"Error parsing CIS file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, fields: List[str], line_num: int) -> Dict[str, Any]:
        """Parse individual CIS transaction line"""
        try:
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"CIS line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference from field 2 (index 1)
            atm_ref_field = fields[1].strip()
            clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
            
            if len(clean_ref) < 4:
                logger.warning(f"CIS line {line_num}: Invalid ATM reference format: {atm_ref_field}")
                return None
            
            atm_ref = clean_ref[:4]  # First 4 digits for grouping
            full_atm_ref = clean_ref  # Full reference
            
            # Extract amount from field 3 (index 2)
            amount = self._extract_amount(fields, line_num)
            
            # Extract date from field 1 (index 0)
            date = self._extract_date(fields, line_num)
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'full_atm_ref': full_atm_ref,
                'amount': amount,
                'date': date
            }
            
        except Exception as e:
            logger.error(f"Error parsing CIS line {line_num}: {str(e)}")
            return None
    
    def _extract_amount(self, fields: List[str], line_num: int) -> float:
        """Extract amount from CIS fields (field 3, index 2)"""
        try:
            if len(fields) > 2:
                amount_str = fields[2].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found CIS amount: {amount} from {fields[2]}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract CIS amount from line {line_num}: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str], line_num: int) -> str:
        """Extract date from CIS fields (field 1, index 0)"""
        try:
            if len(fields) > 0:
                date_str = fields[0].strip()
                if date_str:
                    # If date contains time (separated by comma or space), take only the date part
                    date_parts = re.split('[, ]', date_str)
                    if date_parts:
                        date_str = date_parts[0].strip()
                    logger.debug(f"Found CIS date: {date_str}")
                    return date_str
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract CIS date from line {line_num}: {str(e)}")
        
        return 'N/A'
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches CIS format"""
        try:
            # Check for caret separator
            if self.separator not in line:
                return False
            
            # Split by caret and check minimum fields
            fields = [f.strip() for f in line.split(self.separator)]
            if len(fields) < self.min_fields:
                return False
            
            # Check for valid date format in field 1 (index 0)
            if len(fields) > 0:
                date_str = fields[0].strip()
                # Check for common date formats: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
                if not re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', date_str):
                    return False
            
            # Check for valid ATM reference in field 2 (index 1)
            if len(fields) > 1:
                atm_ref_field = fields[1].strip()
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                if len(clean_ref) < 4:
                    return False
            
            # Check for valid amount in field 3 (index 2)
            if len(fields) > 2:
                amount_str = fields[2].replace(',', '')
                try:
                    float(amount_str)
                except ValueError:
                    return False
            
            return True
            
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches CIS format"""
        lines = file_content.split('\n')[:10]  # Check first 10 lines
        
        valid_transaction_found = False
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check for valid transaction line
            if self._is_valid_line(line):
                valid_transaction_found = True
                break
        
        return valid_transaction_found
    
    def generate_formatted_report_line(self, transaction: Dict[str, Any]) -> str:
        """Generate formatted line for CIS report"""
        try:
            # For CIS, we return the original line as it's already in the correct format
            return f"{transaction['raw_text']}\n"
            
        except Exception as e:
            logger.error(f"Error formatting CIS report line: {str(e)}")
            return f"{transaction['raw_text']}\n"
