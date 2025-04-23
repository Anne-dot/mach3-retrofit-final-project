#!/usr/bin/env python3
"""
Tool Data Backup System for Mach3 CNC Retrofit Project.

This module manages the creation, rotation, and restoration of tool data backups.
It implements a lightweight OOP approach with separate classes for backup management,
rotation, and command-line interface functionality.

Usage:
    python backup_manager.py --create path/to/file.csv
    python backup_manager.py --restore path/to/backup.csv path/to/target.csv
    python backup_manager.py --list
"""

import os
import sys
import shutil
import datetime
import argparse
import logging
import time
from pathlib import Path
from file_lock import FileLock

# Configure logging
log_dir = r"C:\Mach3\ToolManagement\Logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "backup_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class BackupRotation:
    """
    Manages backup file rotation and pruning.
    
    This class is responsible for listing backups and removing
    old backups beyond the maximum limit.
    """
    
    def __init__(self, backup_dir, max_backups=10):
        """
        Initialize the backup rotation manager.
        
        Args:
            backup_dir: Directory where backups are stored
            max_backups: Maximum number of backups to keep (default: 20)
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def list_backups(self):
        """
        List all backup files with creation times.
        
        Returns:
            list: List of dictionaries with 'path' and 'timestamp' keys,
                 sorted by timestamp (newest first)
        """
        backups = []
        
        try:
            # Get all CSV files in backup directory
            for file in os.listdir(self.backup_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(self.backup_dir, file)
                    creation_time = os.path.getctime(file_path)
                    
                    backups.append({
                        'path': file_path,
                        'timestamp': creation_time,
                        'datetime': datetime.datetime.fromtimestamp(creation_time),
                        'filename': file
                    })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logging.error(f"Error listing backups: {str(e)}")
        
        return backups
    
    def prune(self):
        """
        Remove old backups beyond the maximum limit.
        
        Returns:
            int: Number of backups removed
        """
        try:
            backups = self.list_backups()
            
            # If we have more backups than the limit, remove the oldest ones
            if len(backups) > self.max_backups:
                backups_to_remove = backups[self.max_backups:]
                
                for backup in backups_to_remove:
                    try:
                        os.remove(backup['path'])
                        logging.info(f"Removed old backup: {backup['filename']}")
                    except Exception as e:
                        logging.error(f"Error removing backup {backup['path']}: {str(e)}")
                
                return len(backups_to_remove)
            
            return 0
            
        except Exception as e:
            logging.error(f"Error pruning backups: {str(e)}")
            return 0


class BackupManager:
    """
    Manages backup operations for tool data files.
    
    This class creates and restores backups, using the BackupRotation
    class to handle backup file rotation.
    """
    
    def __init__(self, backup_dir=None, max_backups=10, lock_timeout=1800):
        """
        Initialize the backup manager.
        
        Args:
            backup_dir: Directory where backups are stored (default: C:\\Mach3\\ToolManagement\\Backups\\ToolData)
            max_backups: Maximum number of backups to keep (default: 20)
            lock_timeout: Timeout for file locks in seconds (default: 30 minutes)
        """
        # Set default backup directory if not provided
        if backup_dir is None:
            backup_dir = r"C:\Mach3\ToolManagement\Backups\ToolData"
        
        self.backup_dir = backup_dir
        self.lock_timeout = lock_timeout
        
        # Initialize rotation manager
        self.rotation = BackupRotation(backup_dir, max_backups)
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, file_path):
        """
        Create a timestamped backup of the specified file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            dict: Result containing status and message
        """
        try:
            # Verify the source file exists
            if not os.path.exists(file_path):
                return {
                    'status': 'ERROR',
                    'message': f"Source file does not exist: {file_path}"
                }
            
            # Get file name and generate backup file name with timestamp
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(self.backup_dir, backup_file_name)
            
            # Acquire file lock on the source file
            file_lock = FileLock(file_path, self.lock_timeout)

            # Add right before trying to check file lock
            print(f"DEBUG: Checking if file is locked: {file_path}")
            file_locked, lock_info = file_lock.check_file_lock()
            print(f"DEBUG: Lock check result: {file_locked}, Info: {lock_info}")
            
            # Explicitly check if file is locked first
            file_locked, lock_info = file_lock.check_file_lock()
            if file_locked:
                logging.warning(f"Cannot create backup: {file_path} is locked: {lock_info}")
                return {
                    'status': 'ERROR',
                    'message': f"Could not backup file: {file_path} is currently in use by another application"
                }
    
            # Then try to acquire the lock
            if not file_lock.acquire():
                return {
                    'status': 'ERROR',
                    'message': f"Could not acquire lock on {file_path}. File may be in use."
                }
            
            try:
                # Create backup
                shutil.copy2(file_path, backup_path)
                logging.info(f"Created backup: {backup_file_name}")
                
                # Prune old backups
                removed_count = self.rotation.prune()
                if removed_count > 0:
                    logging.info(f"Removed {removed_count} old backup(s)")
                
                return {
                    'status': 'SUCCESS',
                    'message': f"Backup created: {backup_file_name}",
                    'backup_path': backup_path
                }
                
            finally:
                # Always release the lock
                file_lock.release()
                
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return {
                'status': 'ERROR',
                'message': f"Backup failed: {str(e)}"
            }
    
    def restore_from_backup(self, backup_path, target_path):
        """
        Restore a file from a backup.
        
        Args:
            backup_path: Path to the backup file
            target_path: Path where the file should be restored
            
        Returns:
            dict: Result containing status and message
        """
        try:
            # Verify the backup file exists
            if not os.path.exists(backup_path):
                return {
                    'status': 'ERROR',
                    'message': f"Backup file does not exist: {backup_path}"
                }
            
            # Create safety backup of current file if it exists
            safety_backup = None
            if os.path.exists(target_path):
                # Create a safety backup with a special name
                target_name = os.path.basename(target_path)
                name, ext = os.path.splitext(target_name)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_name = f"{name}_prerestore_{timestamp}{ext}"
                safety_backup = os.path.join(self.backup_dir, safety_name)
                
                # Acquire lock on target file
                file_lock = FileLock(target_path, self.lock_timeout)
                if not file_lock.acquire():
                    return {
                        'status': 'ERROR',
                        'message': f"Could not acquire lock on {target_path}. File may be in use."
                    }
                
                try:
                    # Create safety backup
                    shutil.copy2(target_path, safety_backup)
                    logging.info(f"Created safety backup before restore: {safety_name}")
                    
                    # Copy backup to target
                    shutil.copy2(backup_path, target_path)
                    logging.info(f"Restored from backup: {os.path.basename(backup_path)}")
                    
                    return {
                        'status': 'SUCCESS',
                        'message': f"Restored from backup: {os.path.basename(backup_path)}",
                        'safety_backup': safety_backup
                    }
                    
                finally:
                    # Always release the lock
                    file_lock.release()
            else:
                # Target doesn't exist, just copy the backup
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(backup_path, target_path)
                logging.info(f"Restored from backup (target did not exist): {os.path.basename(backup_path)}")
                
                return {
                    'status': 'SUCCESS',
                    'message': f"Restored from backup: {os.path.basename(backup_path)}"
                }
                
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return {
                'status': 'ERROR',
                'message': f"Restore failed: {str(e)}"
            }
    
    def list_backups(self):
        """
        List all available backups.
        
        Returns:
            list: List of dictionaries with backup information
        """
        return self.rotation.list_backups()


def write_status_file(status, message=""):
    """
    Write status file for Mach3 VBScript to read.
    
    Args:
        status: Status string (SUCCESS, ERROR)
        message: Optional message
    """
    status_file = os.path.join(log_dir, "backup_status.txt")
    
    try:
        with open(status_file, 'w') as f:
            f.write(f"{status}\n")
            if message:
                f.write(message)
    except Exception as e:
        logging.error(f"Error writing status file: {str(e)}")


def main():
    """
    Main function that processes command line arguments and executes operations.
    """
    parser = argparse.ArgumentParser(description="Tool Data Backup Manager")
    
    # Add exclusive command arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create', help='Create a backup of the specified file')
    group.add_argument('--restore', help='Restore from a backup file')
    group.add_argument('--list', action='store_true', help='List available backups')
    
    # Add target path for restore operation
    parser.add_argument('--target', help='Target path for restore operation')
    
    # Add status file option for VBScript integration
    parser.add_argument('--status-file', action='store_true', 
                        help='Write result to status file for VBScript')
    
    args = parser.parse_args()
    
    # Create backup manager
    backup_manager = BackupManager()
    
    result = None
    
    if args.create:
        # Create backup
        result = backup_manager.create_backup(args.create)
        print(f"{result['status']}: {result['message']}")
        
    elif args.restore:
        # Verify target path is provided
        if not args.target:
            print("ERROR: Target path is required for restore operation")
            parser.print_help()
            sys.exit(1)
            
        # Restore from backup
        result = backup_manager.restore_from_backup(args.restore, args.target)
        print(f"{result['status']}: {result['message']}")
        
    elif args.list:
        # List backups
        backups = backup_manager.list_backups()
        
        if not backups:
            print("No backups found")
            result = {'status': 'SUCCESS', 'message': 'No backups found'}
        else:
            print(f"Found {len(backups)} backup(s):")
            for i, backup in enumerate(backups, 1):
                date_str = backup['datetime'].strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i}. {backup['filename']} - {date_str}")
            
            result = {'status': 'SUCCESS', 'message': f"Listed {len(backups)} backup(s)"}
    
    # Write status file for VBScript if requested
    if args.status_file and result:
        write_status_file(result['status'], result['message'])
    
    # Return exit code based on result
    return 0 if result and result['status'] == 'SUCCESS' else 1


if __name__ == "__main__":
    sys.exit(main())
