"""
Cross-platform path handling utilities for the CNC milling project.

This module provides consistent path handling functionality that works
identically across Windows and Linux environments to support both
development and production environments.

Classes:
    PathUtils: Main class for path operations and directory management
"""

import os
import sys
import platform
from pathlib import Path


class PathUtils:
    """
    Handles cross-platform path operations for the CNC milling project.
    
    This class provides methods for consistent path handling, directory
    creation, and path normalization across different operating systems.
    """
    
    @staticmethod
    def get_project_root():
        """
        Returns the absolute path to the project root directory.
        
        Works in both development and production environments by traversing
        up the directory tree to find the project root.
        
        Returns:
            Path: Absolute path to project root directory
        """
        # Start with current file's directory
        current_dir = Path(__file__).resolve().parent
        
        # Check if we're in the standard project structure
        # If in Utils/path_utils.py, go up two levels
        parent_dir = current_dir.parent
        
        # If we detect we're in a package structure like Utils, go up one more level
        if parent_dir.name in ('Utils', 'utils'):
            return parent_dir.parent
        
        # Special case for Mach3 environment
        if platform.system() == 'Windows':
            # Check if we're in the expected Mach3 directory structure
            # C:\Mach3\ToolManagement\Scripts\Utils\path_utils.py
            if 'Mach3' in current_dir.parts:
                # Find Mach3 in the path and return its parent
                for i, part in enumerate(current_dir.parts):
                    if part == 'Mach3':
                        return Path(*current_dir.parts[:i+1])
        
        # Default fallback - go up two levels 
        return current_dir.parent.parent
    
    @classmethod
    def get_data_dir(cls):
        """
        Returns the path to the data directory, creating it if it doesn't exist.
        
        Returns:
            Path: Absolute path to the data directory
        """
        root_dir = cls.get_project_root()
        
        if platform.system() == 'Windows' and 'Mach3' in root_dir.parts:
            # In Mach3 production environment
            data_dir = root_dir / "ToolManagement" / "Data"
        else:
            # In development environment
            data_dir = root_dir / "data"
        
        # Create directory if it doesn't exist
        cls.ensure_dir(data_dir)
        return data_dir
    
    @classmethod
    def get_logs_dir(cls):
        """
        Returns the path to the logs directory, creating it if it doesn't exist.
        
        Returns:
            Path: Absolute path to the logs directory
        """
        root_dir = cls.get_project_root()
        
        if platform.system() == 'Windows' and 'Mach3' in root_dir.parts:
            # In Mach3 production environment
            logs_dir = root_dir / "ToolManagement" / "Logs"
        else:
            # In development environment
            logs_dir = root_dir / "logs"
        
        # Create directory if it doesn't exist
        cls.ensure_dir(logs_dir)
        return logs_dir
    
    @classmethod
    def get_test_data_dir(cls):
        """
        Returns the path to the test data directory, creating it if it doesn't exist.
        
        Returns:
            Path: Absolute path to the test data directory
        """
        root_dir = cls.get_project_root()
        
        if platform.system() == 'Windows' and 'Mach3' in root_dir.parts:
            # In Mach3 production environment
            test_data_dir = root_dir / "ToolManagement" / "Scripts" / "Tests" / "TestData"
        else:
            # In development environment
            test_data_dir = root_dir / "tests" / "data"
        
        # Create directory if it doesn't exist
        cls.ensure_dir(test_data_dir)
        return test_data_dir
    
    @staticmethod
    def ensure_dir(path):
        """
        Ensures a directory exists, creating it if needed.
        
        Args:
            path: Path to the directory to ensure
            
        Returns:
            Path: The same path that was passed in
        """
        # Convert string paths to Path objects
        if isinstance(path, str):
            path = Path(path)
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def normalize_path(path):
        """
        Normalizes a path for the current platform.
        
        Args:
            path: Path to normalize (string or Path object)
            
        Returns:
            str: Normalized path string for current platform
        """
        # Convert Path objects to strings
        if isinstance(path, Path):
            path = str(path)
        
        # Handle platform differences
        if platform.system() == 'Windows':
            # Ensure Windows-style paths with backslashes
            return os.path.normpath(path).replace('/', '\\')
        else:
            # Ensure Unix-style paths with forward slashes
            return os.path.normpath(path).replace('\\', '/')
    
    @classmethod
    def relative_to_absolute(cls, relative_path, base_path=None):
        """
        Converts a relative path to an absolute path.
        
        Args:
            relative_path: Relative path to convert
            base_path: Base path to resolve against (default: current working directory)
            
        Returns:
            Path: Absolute path
        """
        # Handle base path
        if base_path is None:
            base_path = Path.cwd()
        elif isinstance(base_path, str):
            base_path = Path(base_path)
        
        # Convert relative path to Path object if it's a string
        if isinstance(relative_path, str):
            relative_path = Path(relative_path)
        
        # Resolve relative path against base path
        return (base_path / relative_path).resolve()
