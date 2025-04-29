"""
Error handling utilities for the CNC milling project.

This module provides standardized error handling, custom exceptions,
and error categorization to ensure consistent error management
across the application.

Classes:
    ErrorCategory: Enum of error categories
    ErrorSeverity: Enum of error severity levels
    BaseError: Base exception class for all custom exceptions
    FileError: Exception for file-related errors
    ValidationError: Exception for data validation errors
    ConfigurationError: Exception for configuration errors
    ErrorHandler: Main class for error handling operations
"""

import os
import sys
import traceback
import enum
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple


class ErrorCategory(enum.Enum):
    """Enumeration of error categories for classification."""
    FILE = "FILE"
    VALIDATION = "VALIDATION"
    CONFIGURATION = "CONFIGURATION"
    PROCESSING = "PROCESSING"
    SYSTEM = "SYSTEM"
    TRANSFORMATION = "TRANSFORMATION"
    UNKNOWN = "UNKNOWN"


class ErrorSeverity(enum.Enum):
    """Enumeration of error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseError(Exception):
    """
    Base exception class for all custom exceptions.
    
    This provides consistent error information across all derived exceptions.
    
    Attributes:
        message (str): Human-readable error description
        category (ErrorCategory): Error category for classification
        severity (ErrorSeverity): Error severity level
        details (Dict): Additional error details
    """
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a BaseError.
        
        Args:
            message: Human-readable error description
            category: Error category for classification (default: UNKNOWN)
            severity: Error severity level (default: ERROR)
            details: Additional error details (default: None)
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        """Return string representation of the error."""
        return f"{self.severity.value} [{self.category.value}]: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details
        }


class FileError(BaseError):
    """Exception raised for file-related errors."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[Union[str, Path]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a FileError.
        
        Args:
            message: Human-readable error description
            file_path: Path to the file causing the error (default: None)
            severity: Error severity level (default: ERROR)
            details: Additional error details (default: None)
        """
        if details is None:
            details = {}
        
        if file_path:
            details["file_path"] = str(file_path)
        
        super().__init__(
            message=message,
            category=ErrorCategory.FILE,
            severity=severity,
            details=details
        )


class ValidationError(BaseError):
    """Exception raised for data validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ValidationError.
        
        Args:
            message: Human-readable error description
            field: Name of the field that failed validation (default: None)
            value: Invalid value that caused the error (default: None)
            severity: Error severity level (default: ERROR)
            details: Additional error details (default: None)
        """
        if details is None:
            details = {}
        
        if field:
            details["field"] = field
        
        if value is not None:  # Allow 0, False, empty string
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=severity,
            details=details
        )


class ConfigurationError(BaseError):
    """Exception raised for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        param: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ConfigurationError.
        
        Args:
            message: Human-readable error description
            param: Name of the configuration parameter (default: None)
            severity: Error severity level (default: ERROR)
            details: Additional error details (default: None)
        """
        if details is None:
            details = {}
        
        if param:
            details["param"] = param
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=severity,
            details=details
        )


class ErrorHandler:
    """
    Handles error processing, formatting, and integration with logging.
    
    This class provides methods for consistent error handling across
    the application, with integration to the logging system.
    """
    
    @staticmethod
    def format_exception(exc: Exception) -> str:
        """
        Format an exception into a human-readable string.
        
        Args:
            exc: Exception to format
            
        Returns:
            str: Formatted exception message with type
        """
        return f"{type(exc).__name__}: {str(exc)}"
    
    @staticmethod
    def get_exception_details(exc: Exception) -> Dict[str, Any]:
        """
        Extract detailed information from an exception.
        
        Args:
            exc: Exception to process
            
        Returns:
            Dict: Dictionary with exception details
        """
        details = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
        
        # Add custom attributes from BaseError
        if isinstance(exc, BaseError):
            details.update({
                "category": exc.category.value,
                "severity": exc.severity.value,
                "details": exc.details
            })
        
        return details
    
    @classmethod
    def handle_exception(
        cls,
        exc: Exception,
        logger=None,
        log_traceback: bool = True
    ) -> Dict[str, Any]:
        """
        Handle an exception with standard formatting and optional logging.
        
        Args:
            exc: Exception to handle
            logger: Logger to use for logging (default: None)
            log_traceback: Whether to include traceback in logs (default: True)
            
        Returns:
            Dict: Standardized error information
        """
        # Get exception details
        error_info = cls.get_exception_details(exc)
        
        # Handle logging if a logger is provided
        if logger:
            if isinstance(exc, BaseError):
                severity = exc.severity
                if severity == ErrorSeverity.CRITICAL:
                    logger.critical(str(exc))
                elif severity == ErrorSeverity.ERROR:
                    logger.error(str(exc))
                elif severity == ErrorSeverity.WARNING:
                    logger.warning(str(exc))
                else:
                    logger.info(str(exc))
            else:
                # For non-custom exceptions, log as error
                logger.error(cls.format_exception(exc))
            
            # Log traceback if enabled
            if log_traceback:
                logger.debug(f"Traceback: {error_info['traceback']}")
        
        return error_info
    
    @staticmethod
    def from_exception(
        exc: Exception,
        default_message: str = "An error occurred"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Create a standard error response from an exception.
        
        This creates a consistent (success, message, details) response
        format used throughout the application.
        
        Args:
            exc: Exception to process
            default_message: Fallback message if exception has no message
            
        Returns:
            Tuple: (success, message, details) where:
                success: Always False for exceptions
                message: Human-readable error message
                details: Dictionary with error details
        """
        # Format the message
        message = str(exc) if str(exc) else default_message
        
        # Get exception details
        if isinstance(exc, BaseError):
            details = exc.to_dict()
        else:
            details = {
                "type": type(exc).__name__,
                "message": message,
                "category": ErrorCategory.UNKNOWN.value,
                "severity": ErrorSeverity.ERROR.value
            }
        
        return False, message, details
    
    @staticmethod
    def create_success_response(
        message: str = "Operation completed successfully",
        data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Create a standard success response.
        
        Args:
            message: Success message
            data: Optional data to include in response
            
        Returns:
            Tuple: (success, message, data) where:
                success: Always True for success responses
                message: Human-readable success message
                data: Dictionary with operation results
        """
        return True, message, data or {}
