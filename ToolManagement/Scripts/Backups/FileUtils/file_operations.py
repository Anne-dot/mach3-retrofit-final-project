"""
File operations utilities for the FileLock system.

This module provides utility functions for common file operations
used by the FileLock class, with proper error handling.
"""

import os
import logging
import time
import random


def create_lock_file(lock_file_path, content_dict):
    """
    Create a lock file with the given content.
    
    Args:
        lock_file_path: Path where lock file should be created
        content_dict: Dictionary of values to write to the lock file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(lock_file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        
        # Write lock file content
        with open(lock_file_path, 'w') as f:
            for key, value in content_dict.items():
                f.write(f"{key}: {value}\n")
                
        return True
    except Exception as e:
        logging.error(f"Error creating lock file {lock_file_path}: {str(e)}")
        return False


def remove_file_safely(file_path, max_retries=3, retry_delay=0.5):
    """
    Remove a file with retry logic for handling temporary access issues.
    
    Args:
        file_path: Path to the file to remove
        max_retries: Maximum number of removal attempts
        retry_delay: Base delay between retries in seconds
        
    Returns:
        bool: True if file was removed successfully, False otherwise
    """
    if not os.path.exists(file_path):
        return True
        
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                logging.error(f"Failed to remove file {file_path} after {max_retries} attempts: {str(e)}")
                return False
            
            # Add jitter to retry delay to prevent synchronization issues
            actual_delay = retry_delay * (1 + attempt) * (1 + random.random())
            logging.info(f"Retrying file removal in {actual_delay:.2f} seconds")
            time.sleep(actual_delay)


def backup_file(file_path, backup_dir=None, max_backups=10):
    """
    Create a timestamped backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backups (default: same as original)
        max_backups: Maximum number of backups to keep
        
    Returns:
        str: Path to backup file if successful, None otherwise
    """
    try:
        if not os.path.exists(file_path):
            logging.warning(f"Cannot backup non-existent file: {file_path}")
            return None
            
        # Get file name and extension
        base_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        
        # Use provided backup directory or default to same directory
        if not backup_dir:
            backup_dir = base_dir
            
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Create timestamped backup file name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Copy file to backup location
        import shutil
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup: {backup_path}")
        
        # Prune old backups if needed
        if max_backups > 0:
            prune_old_backups(backup_dir, name, ext, max_backups)
            
        return backup_path
    except Exception as e:
        logging.error(f"Error creating backup of {file_path}: {str(e)}")
        return None


def prune_old_backups(backup_dir, base_name, extension, max_backups):
    """
    Remove old backup files when there are more than max_backups.
    
    Args:
        backup_dir: Directory containing backups
        base_name: Base name of the file (without timestamp)
        extension: File extension
        max_backups: Maximum number of backups to keep
    """
    try:
        # Get all backup files matching pattern
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith(base_name + "_") and file.endswith(extension):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda x: x[1])
        
        # Remove older backups if we have more than max_backups
        if len(backup_files) > max_backups:
            files_to_remove = backup_files[:-max_backups]  # Keep newest max_backups
            for file_path, _ in files_to_remove:
                remove_file_safely(file_path)
                logging.info(f"Removed old backup: {os.path.basename(file_path)}")
    except Exception as e:
        logging.error(f"Error pruning old backups: {str(e)}")
