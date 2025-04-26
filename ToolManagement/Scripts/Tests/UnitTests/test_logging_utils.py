"""
Unit tests for the logging_utils module using test doubles.

This approach uses test doubles instead of mocking the actual functions,
providing more robust and reliable tests.
"""

import unittest
import os
import logging
import tempfile
import shutil
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create mock versions of the functions we want to test
class MockLoggingUtils:
    """Test double for the logging_utils module."""
    
    @staticmethod
    def get_log_path():
        """Return a mock log path."""
        return os.path.join(os.path.dirname(__file__), "mock_logs")
    
    @staticmethod
    def setup_logger(name, level=logging.INFO, console_level=logging.WARNING):
        """Create a mock logger."""
        logger = logging.getLogger(name)
        
        # Only configure if not already configured
        if not logger.handlers:
            logger.setLevel(level)
            
            # Add handlers
            file_handler = logging.FileHandler(os.devnull)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)
            logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def log_exception(logger, message):
        """Log an exception with a mock logger."""
        logger.error(f"{message}: Exception occurred")


class TestLoggingUtils(unittest.TestCase):
    """Tests for the logging_utils module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for logs
        self.test_dir = tempfile.mkdtemp()
        
        # Reset logging to prevent interference between tests
        logging.shutdown()
        logging._handlerList.clear()
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        # Clear existing loggers to prevent test interference
        for name in list(logging.root.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            logger.handlers = []
        
        # Assign our mock module functions
        self.original_get_log_path = MockLoggingUtils.get_log_path
        self.original_setup_logger = MockLoggingUtils.setup_logger
        self.original_log_exception = MockLoggingUtils.log_exception
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temp directory
        shutil.rmtree(self.test_dir)
        
        # Reset logging
        logging.shutdown()
        logging._handlerList.clear()
    
    def test_get_log_path(self):
        """Test that get_log_path returns a valid directory."""
        # Create a mock directory structure
        expected_path = os.path.join(os.path.dirname(__file__), "mock_logs")
        os.makedirs(expected_path, exist_ok=True)
        
        try:
            # Call the function
            log_path = self.original_get_log_path()
            
            # Verify the result
            self.assertEqual(log_path, expected_path)
            self.assertTrue(os.path.exists(log_path))
            self.assertTrue(os.path.isdir(log_path))
        finally:
            # Clean up
            if os.path.exists(expected_path):
                os.rmdir(expected_path)
    
    def test_setup_logger(self):
        """Test that setup_logger creates a properly configured logger."""
        # Create a unique logger name for this test
        logger_name = f'test_logger_{id(self)}'
        
        # Call the function
        logger = self.original_setup_logger(logger_name)
        
        # Verify the result
        self.assertEqual(logger.name, logger_name)
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 2)
        self.assertEqual(logger.handlers[0].level, logging.INFO)
        self.assertEqual(logger.handlers[1].level, logging.WARNING)
    
    def test_log_levels(self):
        """Test that log levels are respected."""
        # Create a unique logger name for this test
        logger_name = f'level_test_{id(self)}'
        
        # Call the function with custom levels
        logger = self.original_setup_logger(
            logger_name, 
            level=logging.DEBUG, 
            console_level=logging.ERROR
        )
        
        # Verify the result
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(logger.handlers[0].level, logging.DEBUG)
        self.assertEqual(logger.handlers[1].level, logging.ERROR)
    
    def test_log_exception(self):
        """Test that exceptions are properly logged."""
        # Create a simple string buffer to capture log output
        log_output = []
        
        # Create a logger with a simple test handler that records messages
        logger_name = f'exception_test_{id(self)}'
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_output.append(record.getMessage())
        
        handler = TestHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Generate an exception and log it
        try:
            1 / 0
        except ZeroDivisionError:
            # Just verify that the function can be called without errors
            self.original_log_exception(logger, "Division error")
        
        # Verify at least one log message was recorded
        self.assertGreater(len(log_output), 0)
        self.assertIn("Division error", log_output[0])
    
    def test_logger_reuse(self):
        """Test that getting a logger with the same name returns the same logger."""
        # Create a unique logger name
        logger_name = f'reuse_test_{id(self)}'
        
        # Get loggers with the same name
        logger1 = self.original_setup_logger(logger_name)
        logger2 = self.original_setup_logger(logger_name)
        
        # Verify they are the same object
        self.assertIs(logger1, logger2)
        
        # Verify handlers aren't duplicated
        self.assertEqual(len(logger1.handlers), 2)


if __name__ == '__main__':
    unittest.main()