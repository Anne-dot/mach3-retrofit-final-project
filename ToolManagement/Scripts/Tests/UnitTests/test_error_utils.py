"""
Unit tests for the error_utils module.

These tests verify that the error handling utilities work correctly
including custom exceptions, error categorization, and formatting.
"""

import unittest
import os
import sys
import logging

# Add parent directory to path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test
from Utils.error_utils import (
    ErrorCategory, ErrorSeverity, BaseError, FileError,
    ValidationError, ConfigurationError, ErrorHandler
)


class TestErrorUtilsExceptions(unittest.TestCase):
    """Tests for the custom exception classes."""
    
    def test_base_error(self):
        """Test BaseError creation and functionality."""
        # Create a basic error
        error = BaseError("Test error message")
        
        # Check default values
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.category, ErrorCategory.UNKNOWN)
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        self.assertEqual(error.details, {})
        
        # Check string representation
        self.assertEqual(str(error), "ERROR [UNKNOWN]: Test error message")
        
        # Check dictionary conversion
        error_dict = error.to_dict()
        self.assertEqual(error_dict["message"], "Test error message")
        self.assertEqual(error_dict["category"], "UNKNOWN")
        self.assertEqual(error_dict["severity"], "ERROR")
        self.assertEqual(error_dict["details"], {})
        
        # Test with all parameters
        details = {"param1": "value1", "param2": 123}
        error = BaseError(
            message="Custom error", 
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL, 
            details=details
        )
        
        self.assertEqual(error.message, "Custom error")
        self.assertEqual(error.category, ErrorCategory.SYSTEM)
        self.assertEqual(error.severity, ErrorSeverity.CRITICAL)
        self.assertEqual(error.details, details)
    
    def test_file_error(self):
        """Test FileError creation and functionality."""
        # Create a basic file error
        error = FileError("File not found")
        
        # Check defaults and inheritance
        self.assertEqual(error.message, "File not found")
        self.assertEqual(error.category, ErrorCategory.FILE)
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        self.assertEqual(error.details, {})
        
        # Check with file path
        error = FileError("Cannot open file", file_path="/path/to/file.txt")
        self.assertEqual(error.details["file_path"], "/path/to/file.txt")
        
        # Check severity override
        error = FileError(
            "File corrupted", 
            severity=ErrorSeverity.CRITICAL
        )
        self.assertEqual(error.severity, ErrorSeverity.CRITICAL)
    
    def test_validation_error(self):
        """Test ValidationError creation and functionality."""
        # Create a basic validation error
        error = ValidationError("Invalid data format")
        
        # Check defaults and inheritance
        self.assertEqual(error.message, "Invalid data format")
        self.assertEqual(error.category, ErrorCategory.VALIDATION)
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        self.assertEqual(error.details, {})
        
        # Check with field and value
        error = ValidationError(
            "Value out of range", 
            field="temperature", 
            value=150
        )
        self.assertEqual(error.details["field"], "temperature")
        self.assertEqual(error.details["value"], "150")
        
        # Test with zero value (should be included, not treated as None)
        error = ValidationError("Zero not allowed", field="count", value=0)
        self.assertEqual(error.details["value"], "0")
        
        # Test with empty string value
        error = ValidationError("Empty not allowed", field="name", value="")
        self.assertEqual(error.details["value"], "")
    
    def test_configuration_error(self):
        """Test ConfigurationError creation and functionality."""
        # Create a basic configuration error
        error = ConfigurationError("Missing configuration")
        
        # Check defaults and inheritance
        self.assertEqual(error.message, "Missing configuration")
        self.assertEqual(error.category, ErrorCategory.CONFIGURATION)
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        self.assertEqual(error.details, {})
        
        # Check with param
        error = ConfigurationError(
            "Invalid setting", 
            param="timeout"
        )
        self.assertEqual(error.details["param"], "timeout")


class TestErrorHandler(unittest.TestCase):
    """Tests for the ErrorHandler class."""
    
    def test_format_exception(self):
        """Test exception formatting."""
        # Standard exception
        exc = ValueError("Invalid value")
        formatted = ErrorHandler.format_exception(exc)
        self.assertEqual(formatted, "ValueError: Invalid value")
        
        # Custom exception
        exc = BaseError("Custom error message")
        formatted = ErrorHandler.format_exception(exc)
        self.assertEqual(formatted, "BaseError: ERROR [UNKNOWN]: Custom error message")
    
    def test_get_exception_details(self):
        """Test extracting details from exceptions."""
        # Standard exception
        exc = ValueError("Invalid value")
        details = ErrorHandler.get_exception_details(exc)
        
        self.assertEqual(details["type"], "ValueError")
        self.assertEqual(details["message"], "Invalid value")
        self.assertIn("traceback", details)
        
        # Custom exception
        exc = ValidationError("Invalid data", field="name")
        details = ErrorHandler.get_exception_details(exc)
        
        self.assertEqual(details["type"], "ValidationError")
        self.assertEqual(details["message"], "ERROR [VALIDATION]: Invalid data")
        self.assertEqual(details["category"], "VALIDATION")
        self.assertEqual(details["severity"], "ERROR")
        self.assertEqual(details["details"]["field"], "name")
    
    def test_from_exception(self):
        """Test creating standard response from exceptions."""
        # Standard exception
        exc = ValueError("Invalid value")
        success, message, details = ErrorHandler.from_exception(exc)
        
        self.assertFalse(success)
        self.assertEqual(message, "Invalid value")
        self.assertEqual(details["type"], "ValueError")
        self.assertEqual(details["category"], "UNKNOWN")
        
        # Custom exception
        exc = FileError("File not found", file_path="/tmp/missing.txt")
        success, message, details = ErrorHandler.from_exception(exc)
        
        self.assertFalse(success)
        self.assertEqual(message, "ERROR [FILE]: File not found")
        self.assertEqual(details["category"], "FILE")
        self.assertEqual(details["details"]["file_path"], "/tmp/missing.txt")
        
        # Empty message exception
        class EmptyMessageError(Exception):
            def __str__(self):
                return ""
                
        exc = EmptyMessageError()
        success, message, details = ErrorHandler.from_exception(
            exc, default_message="Fallback message"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Fallback message")
    
    def test_create_success_response(self):
        """Test creating success responses."""
        # Default success
        success, message, data = ErrorHandler.create_success_response()
        
        self.assertTrue(success)
        self.assertEqual(message, "Operation completed successfully")
        self.assertEqual(data, {})
        
        # Custom success with data
        result_data = {"id": 123, "name": "Test"}
        success, message, data = ErrorHandler.create_success_response(
            message="Item created successfully",
            data=result_data
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Item created successfully")
        self.assertEqual(data, result_data)
    
    def test_handle_exception_without_logger(self):
        """Test handling exceptions without a logger."""
        # Standard exception
        exc = ValueError("Test error")
        result = ErrorHandler.handle_exception(exc)
        
        self.assertEqual(result["type"], "ValueError")
        self.assertEqual(result["message"], "Test error")
        self.assertIn("traceback", result)
    
    def test_handle_exception_with_logger(self):
        """Test handling exceptions with logger integration."""
        # Create a test logger that captures logs
        class TestLogger:
            def __init__(self):
                self.logs = []
            
            def error(self, msg):
                self.logs.append(("ERROR", msg))
            
            def warning(self, msg):
                self.logs.append(("WARNING", msg))
            
            def info(self, msg):
                self.logs.append(("INFO", msg))
            
            def critical(self, msg):
                self.logs.append(("CRITICAL", msg))
            
            def debug(self, msg):
                self.logs.append(("DEBUG", msg))
        
        logger = TestLogger()
        
        # Test with standard exception
        exc = ValueError("Standard error")
        ErrorHandler.handle_exception(exc, logger)
        
        # Should log as ERROR
        self.assertEqual(logger.logs[0][0], "ERROR")
        self.assertEqual(logger.logs[0][1], "ValueError: Standard error")
        
        # Check traceback is logged
        self.assertEqual(logger.logs[1][0], "DEBUG")
        self.assertIn("Traceback", logger.logs[1][1])
        
        # Reset logs
        logger.logs = []
        
        # Test with BaseError and different severity levels
        for severity, level in [
            (ErrorSeverity.INFO, "INFO"),
            (ErrorSeverity.WARNING, "WARNING"),
            (ErrorSeverity.ERROR, "ERROR"),
            (ErrorSeverity.CRITICAL, "CRITICAL")
        ]:
            exc = BaseError(f"{level} message", severity=severity)
            ErrorHandler.handle_exception(exc, logger)
            
            # Check correct log level
            self.assertEqual(logger.logs[0][0], level)
            
            # Reset logs
            logger.logs = []
        
        # Test without traceback
        exc = ValueError("No traceback error")
        ErrorHandler.handle_exception(exc, logger, log_traceback=False)
        
        # Should only have error message, no traceback
        self.assertEqual(len(logger.logs), 1)
        self.assertEqual(logger.logs[0][0], "ERROR")


if __name__ == '__main__':
    unittest.main()
