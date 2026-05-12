from flask import request, jsonify
import logging
from werkzeug.utils import secure_filename
from typing import Type, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class GenericFileProcessor:
    """Generic file processor that handles common file processing logic for all parsers"""
    
    @staticmethod
    def read_file_with_encoding_fallback(file) -> str:
        """Read file content with encoding fallback"""
        # Read bytes first, then decode to avoid file pointer issues
        file.seek(0)  # Reset file pointer to beginning
        content_bytes = file.read()
        
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, try with errors='ignore'
        return content_bytes.decode('utf-8', errors='ignore')
    
    @staticmethod
    def validate_file_request() -> Tuple[bool, str, Any]:
        """Validate that file is present in request"""
        if 'file' not in request.files:
            return False, 'No file provided', None
        
        file = request.files['file']
        if file.filename == '':
            return False, 'No file selected', None
        
        return True, '', file
    
    @staticmethod
    def process_file_generic(parser_class: Type, route_name: str, 
                           validation_error_message: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generic file processing logic that can be used by any parser route
        
        Args:
            parser_class: The parser class to use (e.g., BDOParser)
            route_name: Name of the route for logging (e.g., 'BDO')
            validation_error_message: Custom validation error message
            
        Returns:
            Tuple of (success, error_message, result_data)
        """
        try:
            # Validate file request
            is_valid, error_msg, file = GenericFileProcessor.validate_file_request()
            if not is_valid:
                return False, error_msg, {}
            
            # Get original filename
            original_filename = secure_filename(file.filename)
            
            # Read file content with encoding fallback
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            
            # Create parser instance and validate file format
            parser = parser_class()
            try:
                if not parser.validate_file_format(file_content):
                    default_error = f'File does not match {route_name} format.'
                    error_message = validation_error_message or default_error
                    return False, error_message, {}
            except ValueError as e:
                # For ValueError from validate_file_format (like split line errors), return the detailed message directly
                logger.error(f"Validation error in {route_name} file format: {str(e)}")
                return False, str(e), {}
            
            # Parse the file
            result = parser.parse_file(file_content)
            
            # Add filename to result
            result['original_filename'] = original_filename
            
            logger.info(f"{route_name} file {original_filename} processed successfully")
            return True, '', result
            
        except ValueError as e:
            # For ValueError from parser validation, return the detailed message directly
            logger.error(f"Validation error in {route_name} file: {str(e)}")
            return False, str(e), {}
        except Exception as e:
            logger.error(f"Error processing {route_name} file: {str(e)}")
            return False, f'Processing failed: {str(e)}', {}
    
    @staticmethod
    def validate_file_generic(parser_class: Type, route_name: str, 
                            requirements: list = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generic file validation logic that can be used by any parser route
        
        Args:
            parser_class: The parser class to use
            route_name: Name of the route for logging
            requirements: List of validation requirements for error messages
            
        Returns:
            Tuple of (success, error_message, validation_data)
        """
        try:
            # Validate file request
            is_valid, error_msg, file = GenericFileProcessor.validate_file_request()
            if not is_valid:
                return False, error_msg, {}
            
            # Read file content with encoding fallback
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            
            # Create parser instance and validate file format
            parser = parser_class()
            is_valid = parser.validate_file_format(file_content)
            
            if is_valid:
                # Get additional info for valid files
                lines = file_content.split('\n')
                non_empty_lines = [line for line in lines if line.strip()]
                
                validation_data = {
                    'valid': True,
                    'message': f'File format is valid for {route_name} processing',
                    'file_info': {
                        'total_lines': len(lines),
                        'non_empty_lines': len(non_empty_lines),
                        'first_line': non_empty_lines[0] if non_empty_lines else None
                    }
                }
                return True, '', validation_data
            else:
                # Return validation failure
                validation_data = {
                    'valid': False,
                    'message': f'File does not match {route_name} format',
                    'requirements': requirements or []
                }
                return False, '', validation_data
                
        except Exception as e:
            logger.error(f"Error validating {route_name} file: {str(e)}")
            return False, f'Validation failed: {str(e)}', {}
