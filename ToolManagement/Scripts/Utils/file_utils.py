"""
File handling utilities for the CNC milling project.

This module provides safe file operations with locking mechanisms
to prevent concurrent access issues across the application.

Classes:
    FileLock: Provides file locking capabilities
    FileUtils: Main class for safe file operations
"""

import os
import sys
import time
import json
import csv
import shutil
import platform
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple, BinaryIO, TextIO, Iterator

# Import project utilities
try:
    from Utils.error_utils import FileError, ErrorSeverity, ErrorHandler
    from Utils.path_utils import PathUtils
except ImportError:
    # Add parent directory to path for standalone testing
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from error_utils import FileError, ErrorSeverity, ErrorHandler
    from path_utils import PathUtils


class FileLock:
    """
    Provides file locking mechanism to prevent concurrent access.
    
    This class implements a simple file-based locking system that works
    across platforms and prevents multiple processes from accessing
    the same file simultaneously.
    """
    
    def __init__(self, file_path: Union[str, Path], timeout: float = 30.0):
        """
        Initialize a file lock for the specified file.
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time in seconds to wait for lock acquisition (default: 30)
        """
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.with_suffix(self.file_path.suffix + '.lock')
        self.timeout = timeout
        self.acquired = False
    
    def acquire(self) -> bool:
        """
        Acquire a lock on the file.
        
        Returns:
            bool: True if lock was acquired, False otherwise
        
        Raises:
            FileError: If lock path creation fails
        """
        if self.acquired:
            return True
        
        start_time = time.time()
        
        # Try to acquire lock until timeout
        while time.time() - start_time < self.timeout:
            try:
                # Check if lock file exists and is fresh
                if self.lock_path.exists():
                    # Check if lock is stale
                    lock_age = time.time() - self.lock_path.stat().st_mtime
                    if lock_age > self.timeout:
                        # Lock is stale, remove it
                        self.lock_path.unlink()
                    else:
                        # Lock is fresh, wait and retry
                        time.sleep(0.1)
                        continue
                
                # Create lock file with process information
                with open(self.lock_path, 'w') as f:
                    lock_info = {
                        'pid': os.getpid(),
                        'hostname': platform.node(),
                        'created': time.time()
                    }
                    f.write(json.dumps(lock_info))
                
                # Verify the lock was created by us
                with open(self.lock_path, 'r') as f:
                    lock_data = json.loads(f.read())
                    if lock_data['pid'] == os.getpid():
                        self.acquired = True
                        return True
            
            except Exception as e:
                error_msg = f"Failed to acquire lock for {self.file_path.name}"
                raise FileError(
                    message=error_msg,
                    file_path=str(self.file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            
            # Wait before retrying
            time.sleep(0.1)
        
        # Timeout expired
        return False
    
    def release(self) -> bool:
        """
        Release the lock if it is held.
        
        Returns:
            bool: True if lock was released, False if it wasn't held
        """
        if not self.acquired:
            return False
        
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
            self.acquired = False
            return True
        except Exception:
            return False
    
    def __enter__(self):
        """Enter context manager."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.release()
    
    def __del__(self):
        """Ensure lock is released when object is garbage collected."""
        self.release()


class FileUtils:
    """
    Provides utilities for safe file operations with locking.
    
    This class implements methods for reading, writing, and managing
    files safely with proper error handling and locking.
    """
    
    @staticmethod
    def read_text(
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        use_lock: bool = True,
        lock_timeout: float = 30.0
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Read text from a file safely with optional locking.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            
        Returns:
            Tuple: (success, content, details) where:
                success: True if read was successful, False otherwise
                content: File content if successful, error message otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        
        try:
            # Check if file exists
            if not file_path.exists():
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"File not found: {file_path.name}",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout}
                        )
                    )
            
            # Read file content
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            return ErrorHandler.create_success_response(
                message=f"Successfully read {file_path.name}",
                data={"content": content, "size": len(content)}
            )
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to read {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
    
    @staticmethod
    def write_text(
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Write text to a file safely with optional locking and backup.
        
        Args:
            file_path: Path to the file to write
            content: Text content to write
            encoding: File encoding (default: utf-8)
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)
            
        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None
        
        try:
            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout}
                        )
                    )
            
            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(
                    f"{file_path.stem}_{timestamp}{file_path.suffix}"
                )
                shutil.copy2(file_path, backup_path)
            
            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Replace the original file with the temporary file
            if platform.system() == 'Windows' and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()
            
            temp_file.rename(file_path)
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            result_details = {"size": len(content)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)
            
            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {file_path.name}",
                data=result_details
            )
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
    
    @staticmethod
    def read_binary(
        file_path: Union[str, Path],
        use_lock: bool = True,
        lock_timeout: float = 30.0
    ) -> Tuple[bool, bytes, Dict[str, Any]]:
        """
        Read binary data from a file safely with optional locking.
        
        Args:
            file_path: Path to the file to read
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            
        Returns:
            Tuple: (success, content, details) where:
                success: True if read was successful, False otherwise
                content: Binary data if successful, empty bytes otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        
        try:
            # Check if file exists
            if not file_path.exists():
                return False, b'', {
                    "error": f"File not found: {file_path.name}",
                    "file_path": str(file_path)
                }
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return False, b'', {
                        "error": f"Could not acquire lock for {file_path.name}",
                        "file_path": str(file_path),
                        "timeout": lock_timeout
                    }
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            return True, content, {"size": len(content)}
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return False, b'', {
                "error": str(e),
                "file_path": str(file_path)
            }
    
    @staticmethod
    def write_binary(
        file_path: Union[str, Path],
        data: bytes,
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Write binary data to a file safely with optional locking and backup.
        
        Args:
            file_path: Path to the file to write
            data: Binary data to write
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)
            
        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None
        
        try:
            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout}
                        )
                    )
            
            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(
                    f"{file_path.stem}_{timestamp}{file_path.suffix}"
                )
                shutil.copy2(file_path, backup_path)
            
            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, 'wb') as f:
                f.write(data)
            
            # Replace the original file with the temporary file
            if platform.system() == 'Windows' and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()
            
            temp_file.rename(file_path)
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            result_details = {"size": len(data)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)
            
            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {file_path.name}",
                data=result_details
            )
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
    
    @staticmethod
    def read_csv(
        file_path: Union[str, Path],
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        **csv_options
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Read a CSV file safely with optional locking.
        
        Args:
            file_path: Path to the CSV file to read
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            **csv_options: Additional options to pass to csv.DictReader
            
        Returns:
            Tuple: (success, rows, details) where:
                success: True if read was successful, False otherwise
                rows: List of row dictionaries if successful, empty list otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        
        try:
            # Check if file exists
            if not file_path.exists():
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"CSV file not found: {file_path.name}",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout}
                        )
                    )
            
            # Read CSV content
            rows = []
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f, **csv_options)
                rows = list(reader)
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            return ErrorHandler.create_success_response(
                message=f"Successfully read {len(rows)} rows from {file_path.name}",
                data={"rows": rows, "count": len(rows)}
            )
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to read CSV {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
    
    @staticmethod
    def write_csv(
        file_path: Union[str, Path],
        rows: List[Dict[str, Any]],
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False,
        fieldnames: Optional[List[str]] = None,
        **csv_options
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Write rows to a CSV file safely with optional locking and backup.
        
        Args:
            file_path: Path to the CSV file to write
            rows: List of dictionaries, each representing a row
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)
            fieldnames: List of field names for the CSV header (default: None)
            **csv_options: Additional options to pass to csv.DictWriter
            
        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None
        
        try:
            # Determine fieldnames if not provided
            if fieldnames is None and rows:
                fieldnames = list(rows[0].keys())
            
            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)
            
            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout}
                        )
                    )
            
            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(
                    f"{file_path.stem}_{timestamp}{file_path.suffix}"
                )
                shutil.copy2(file_path, backup_path)
            
            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, **csv_options)
                writer.writeheader()
                writer.writerows(rows)
            
            # Replace the original file with the temporary file
            if platform.system() == 'Windows' and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()
            
            temp_file.rename(file_path)
            
            # Release lock if used
            if use_lock:
                lock.release()
            
            result_details = {"count": len(rows)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)
            
            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {len(rows)} rows to {file_path.name}",
                data=result_details
            )
        
        except Exception as e:
            # Ensure lock is released if used
            if use_lock and 'lock' in locals() and lock.acquired:
                lock.release()
            
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write CSV {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
    
    @staticmethod
    def ensure_backup_dir(
        base_dir: Union[str, Path],
        max_backups: int = 20
    ) -> Tuple[bool, Path, Dict[str, Any]]:
        """
        Ensure a backup directory exists and manage the number of backups.
        
        Args:
            base_dir: Base directory where backups should be stored
            max_backups: Maximum number of backup files to keep (default: 20)
            
        Returns:
            Tuple: (success, backup_dir, details) where:
                success: True if operation was successful, False otherwise
                backup_dir: Path to the backup directory
                details: Dictionary with operation details or error information
        """
        try:
            base_dir = Path(base_dir)
            backup_dir = base_dir / "backups"
            
            # Create backup directory if it doesn't exist
            PathUtils.ensure_dir(backup_dir)
            
            # Manage existing backups if max_backups is specified
            if max_backups > 0:
                # Get all backup files sorted by modification time (oldest first)
                backup_files = sorted(
                    backup_dir.glob("*"),
                    key=lambda f: f.stat().st_mtime
                )
                
                # Remove oldest backups if there are too many
                while len(backup_files) > max_backups:
                    oldest = backup_files.pop(0)
                    if oldest.is_file():
                        oldest.unlink()
                    elif oldest.is_dir():
                        shutil.rmtree(oldest)
            
            return ErrorHandler.create_success_response(
                message="Backup directory ready",
                data={"backup_dir": str(backup_dir), "managed": max_backups > 0}
            )
        
        except Exception as e:
            return ErrorHandler.from_exception(
                FileError(
                    message="Failed to manage backup directory",
                    file_path=str(base_dir),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )
