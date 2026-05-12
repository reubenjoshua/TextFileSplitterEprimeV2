import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class BANCNETParser(BaseParser):
    """Parser for BANCNET transaction files"""
    
    def __init__(self):
        super().__init__("BANCNET")
        self.min_line_length = 50
        self.asterisk_marker = '*'
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse BANCNET transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing BANCNET file with {len(lines)} lines")
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                # Skip lines that are too short
                if len(line.strip()) < self.min_line_length:
                    continue
                
                # Skip lines without asterisk markers
                if self.asterisk_marker not in line:
                    continue
                
                raw_contents.append(line)
                
                # Parse the transaction line
                transaction = self._parse_transaction_line(line, line_num)
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
            
            logger.info(f"BANCNET processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
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
            logger.error(f"Error parsing BANCNET file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual BANCNET transaction line"""
        try:
            # Validate line length
            if len(line) < self.min_line_length:
                logger.warning(f"BANCNET line {line_num} is too short: {len(line)} < {self.min_line_length}")
                return None
            
            # Check for asterisk marker
            if self.asterisk_marker not in line:
                logger.warning(f"BANCNET line {line_num} does not contain asterisk marker")
                return None
            
            # Extract ATM reference
            atm_ref = self._extract_atm_reference(line, line_num)
            if not atm_ref:
                return None
            
            # Extract amount
            amount = self._extract_amount(line, line_num)
            
            # Extract date
            date = self._extract_date(line, line_num)
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'full_atm_ref': atm_ref,
                'amount': amount,
                'date': date
            }
            
        except Exception as e:
            logger.error(f"Error parsing BANCNET line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, line: str, line_num: int) -> str:
        """Extract ATM reference from BANCNET line"""
        try:
            # Find the first asterisk position
            asterisk_pos = line.find(self.asterisk_marker)
            if asterisk_pos <= 0 or asterisk_pos < 14:
                logger.warning(f"BANCNET line {line_num}: Invalid asterisk position: {asterisk_pos}")
                return None
            
            # Extract ATM reference (4 characters before the asterisk)
            atm_ref_field = line[asterisk_pos - 14:asterisk_pos - 10]
            if not atm_ref_field.strip():
                logger.warning(f"BANCNET line {line_num}: Empty ATM reference field")
                return None
            
            # Clean the reference (keep only digits)
            clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
            
            if len(clean_ref) < 4:
                logger.warning(f"BANCNET line {line_num}: Invalid ATM reference format: {atm_ref_field}")
                return None
            
            atm_ref = clean_ref[:4]  # First 4 digits for grouping
            logger.debug(f"Found BANCNET ATM ref: {atm_ref} from {atm_ref_field}")
            return atm_ref
            
        except Exception as e:
            logger.error(f"Error extracting BANCNET ATM reference from line {line_num}: {str(e)}")
            return None
    
    def _extract_amount(self, line: str, line_num: int) -> float:
        """Extract amount from BANCNET line"""
        try:
            # Find the last asterisk position
            last_asterisk_pos = line.rfind(self.asterisk_marker)
            if last_asterisk_pos <= 0 or len(line) <= last_asterisk_pos + 28:
                logger.warning(f"BANCNET line {line_num}: Invalid last asterisk position or line too short")
                return 0.0
            
            # Extract amount (8 characters starting from position 21 after the last asterisk)
            amount_str = line[last_asterisk_pos + 21:last_asterisk_pos + 29]
            
            try:
                amount = float(amount_str) / 100  # Convert to decimal
                if 0 < amount < 1000000:  # Basic sanity check
                    logger.debug(f"Found BANCNET amount: {amount} from {amount_str}")
                    return amount
                else:
                    logger.warning(f"BANCNET line {line_num}: Amount out of range: {amount}")
                    return 0.0
            except ValueError:
                logger.warning(f"BANCNET line {line_num}: Could not convert amount: {amount_str}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error extracting BANCNET amount from line {line_num}: {str(e)}")
            return 0.0
    
    def _extract_date(self, line: str, line_num: int) -> str:
        """Extract date from BANCNET line"""
        try:
            # Ensure line is long enough
            if len(line) < 50:
                return 'N/A'
            
            # Get the first 20 characters
            first_20 = line[:20]
            # Get the last 6 digits from the first 20 characters
            date_str = first_20[-6:]
            
            if date_str and date_str.isdigit():
                # Format the date from YYMMDD to MM/DD/2025
                day = date_str[4:6]  # Last 2 digits are the day
                month = date_str[2:4]  # Middle 2 digits are the month
                formatted_date = f"{month}/{day}/2025"
                logger.debug(f"Found BANCNET date: {formatted_date} from {date_str}")
                return formatted_date
            else:
                logger.warning(f"BANCNET line {line_num}: Invalid date format: {date_str}")
                return 'N/A'
                
        except Exception as e:
            logger.error(f"Error extracting BANCNET date from line {line_num}: {str(e)}")
            return 'N/A'
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches BANCNET format"""
        try:
            # Check minimum length
            if len(line.strip()) < self.min_line_length:
                return False
            
            # Check for asterisk marker
            if self.asterisk_marker not in line:
                return False
            
            # Check for valid ATM reference pattern
            asterisk_pos = line.find(self.asterisk_marker)
            if asterisk_pos <= 0 or asterisk_pos < 14:
                return False
            
            # Check for valid amount pattern
            last_asterisk_pos = line.rfind(self.asterisk_marker)
            if last_asterisk_pos <= 0 or len(line) <= last_asterisk_pos + 28:
                return False
            
            # Check for valid date pattern
            if len(line) >= 50:
                first_20 = line[:20]
                date_str = first_20[-6:]
                if not (date_str.isdigit() and len(date_str) == 6):
                    return False
            
            return True
            
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches BANCNET format"""
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
        """Generate formatted line for BANCNET report"""
        try:
            # For BANCNET, we return the original line as it's already in the correct format
            return f"{transaction['raw_text']}\n"
            
        except Exception as e:
            logger.error(f"Error formatting BANCNET report line: {str(e)}")
            return f"{transaction['raw_text']}\n"
