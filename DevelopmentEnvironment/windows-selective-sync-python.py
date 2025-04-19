#!/usr/bin/env python3
r"""
Selective Bidirectional File Synchronization for Mach3 CNC Retrofit Project

This script provides selective two-way synchronization between:
- C:\Mach3 folder (Main Mach3 installation)
- Z:\Mach3 folder (VirtualBox shared folder)

Features:
- Recursive synchronization of specified folders
- Individual file synchronization from any location
- File content change detection using hash comparison
- Timestamp-based conflict resolution with tolerance
- Empty directory handling
- Deletion propagation
- Robust error handling with detailed logging
- Backup of sync state

Usage:
Place this script in C:\Mach3\DevelopmentEnvironment folder
Configure folders and files to sync in the script settings
Configure Task Scheduler to run this at startup
"""

import os
import shutil
import time
import json
import hashlib
import schedule
import logging
import sys
import datetime
import traceback
from pathlib import Path

# Base directory paths
MACH3_DIR = r"C:\Mach3"
SHARED_DIR = r"Z:\Mach3"

# Script location
SCRIPT_DIR = os.path.join(MACH3_DIR, "DevelopmentEnvironment")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

# File to store the last sync state
SYNC_STATE_FILE = os.path.join(SCRIPT_DIR, r"windows-sync\sync_state.json")

# Set a timestamp tolerance for comparing file modification times (in seconds)
TIME_TOLERANCE = 3

# Only sync these specific folders (with all subfolders)
FOLDERS_TO_SYNC = [
    os.path.join("macros", "Mach3Development"),
    "ToolManagement",
    "DevelopmentEnvironment"
]

# Individual files to sync (relative to Mach3 folder)
FILES_TO_SYNC = [
    "LastErrors.txt",
    "python location.txt"
]

# Patterns to ignore
IGNORE_PATTERNS = [
    '*.bak',
    '*.tmp',
    '*Zone.Identifier*',
    '.git/',
    '.gitignore',
    '.gitattributes',
    '.github/',
    '.DS_Store',
    '__pycache__/',
    '*.pyc'
]

# Configure logging
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"sync_{datetime.datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

def should_ignore(path):
    """
    Check if a path should be ignored based on patterns.
    
    Args:
        path: The relative path to check against ignore patterns
        
    Returns:
        bool: True if the path should be ignored, False otherwise
    """
    for pattern in IGNORE_PATTERNS:
        if pattern.endswith('/'):  # Directory pattern
            dir_pattern = pattern[:-1]
            if dir_pattern in path.split(os.sep):
                return True
        elif pattern.startswith('*'):  # Extension pattern
            ext = pattern[1:]
            if path.endswith(ext):
                return True
        else:  # Exact match
            if pattern in path.split(os.sep):
                return True
    return False

def calculate_file_hash(filepath):
    """
    Calculate a hash for the file to detect changes.
    
    Args:
        filepath: Path to the file to hash
        
    Returns:
        str: MD5 hash of the file content or None if error
    """
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {filepath}: {str(e)}")
        return None

def get_all_files(directory, base_path):
    """
    Get a dictionary of all files and directories with their modification times.
    
    Args:
        directory: The directory to scan
        base_path: The base path for creating relative paths
        
    Returns:
        dict: Dictionary mapping relative paths to file/directory information
    """
    result = {}
    
    try:
        # Process all directories first
        for root, dirs, _ in os.walk(directory):
            # Process root directory
            rel_root = os.path.relpath(root, base_path)
            if rel_root != '.' and not should_ignore(rel_root):
                dir_stat = os.stat(root)
                result[rel_root] = {
                    'is_dir': True,
                    'mtime': dir_stat.st_mtime,
                    'hash': None
                }
        
        # Then process all files
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, base_path)
                if should_ignore(relpath):
                    continue
                    
                try:
                    result[relpath] = {
                        'mtime': os.path.getmtime(filepath),
                        'hash': calculate_file_hash(filepath),
                        'is_dir': False
                    }
                except Exception as e:
                    logging.error(f"Error processing file {filepath}: {str(e)}")
    except Exception as e:
        logging.error(f"Error scanning directory {directory}: {str(e)}")
    
    return result

def is_in_sync_folders(path):
    """
    Check if a path is within one of the folders to sync.
    
    Args:
        path: The path to check
        
    Returns:
        bool: True if path is in a sync folder, False otherwise
    """
    for folder in FOLDERS_TO_SYNC:
        normalized_folder = os.path.normpath(folder)
        normalized_path = os.path.normpath(path)
        if normalized_path == normalized_folder or normalized_path.startswith(normalized_folder + os.sep):
            return True
    return False

def load_sync_state():
    """
    Load the previous sync state from file.
    
    Returns:
        dict: The loaded sync state or a default empty state if file doesn't exist
    """
    try:
        if os.path.exists(SYNC_STATE_FILE):
            with open(SYNC_STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading sync state: {str(e)}, starting fresh")
    
    # Initialize with basic structure if file doesn't exist or has an error
    return {
        'folders': {'mach3': {}, 'shared': {}},
        'files': {}
    }

def save_sync_state(sync_states):
    """
    Save the current sync state to file with backup.
    
    Args:
        sync_states: The sync state dictionary to save
    """
    try:
        # Create backup of current state file first if it exists
        if os.path.exists(SYNC_STATE_FILE):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{SYNC_STATE_FILE}.{timestamp}.bak"
            shutil.copy2(SYNC_STATE_FILE, backup_file)
            logging.info(f"Created backup of sync state: {backup_file}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
        
        with open(SYNC_STATE_FILE, 'w') as f:
            json.dump(sync_states, f, indent=2)
        logging.info(f"Sync state saved to {SYNC_STATE_FILE}")
        
        # Clean up old backup files
        cleanup_old_backups()
        
    except Exception as e:
        logging.error(f"ERROR saving sync state: {str(e)}")

def cleanup_old_backups(max_age_hours=1):
    """Clean up backup files older than the specified number of hours."""
    try:
        backup_dir = os.path.dirname(SYNC_STATE_FILE)
        base_name = os.path.basename(SYNC_STATE_FILE)
        # Get list of backup files
        backup_files = [f for f in os.listdir(backup_dir) 
                       if f.startswith(base_name) and f.endswith(".bak")]
        
        # Current time minus max age in seconds
        cutoff_time = time.time() - (max_age_hours * 60 * 60)
        
        # Delete older files
        deleted_count = 0
        for backup_file in backup_files:
            file_path = os.path.join(backup_dir, backup_file)
            if os.path.getmtime(file_path) < cutoff_time:
                os.remove(file_path)
                deleted_count += 1
        
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} backup files older than {max_age_hours} hour(s)")
            
    except Exception as e:
        logging.error(f"Error cleaning up backup files: {str(e)}")

def sync_file(mach3_path, shared_path, relative_path, prev_state=None):
    """
    Sync a single file between Mach3 and shared directories.
    
    Args:
        mach3_path: Full path to the file in Mach3 directory
        shared_path: Full path to the file in shared directory
        relative_path: Relative path for logging and state tracking
        prev_state: Previous sync state for this file
        
    Returns:
        dict: New sync state for this file or None if file no longer exists
    """
    logging.info(f"Syncing file: {relative_path}")
    
    # Check if both files exist
    mach3_exists = os.path.exists(mach3_path)
    shared_exists = os.path.exists(shared_path)
    
    # Initialize previous state if not provided
    if prev_state is None:
        prev_state = {
            'mach3_mtime': 0,
            'shared_mtime': 0,
            'mach3_hash': None,
            'shared_hash': None
        }
    
    # Handle deletion propagation
    if prev_state.get('mach3_exists', False) and prev_state.get('shared_exists', False):
        if mach3_exists and not shared_exists:
            # File was deleted from shared, delete from Mach3 too
            try:
                os.remove(mach3_path)
                logging.info(f"Deleted file from Mach3 (propagated): {relative_path}")
                return None  # Return None to indicate file no longer exists
            except Exception as e:
                logging.error(f"Error deleting file from Mach3: {relative_path} - {str(e)}")
        
        elif not mach3_exists and shared_exists:
            # File was deleted from Mach3, delete from shared too
            try:
                os.remove(shared_path)
                logging.info(f"Deleted file from shared (propagated): {relative_path}")
                return None  # Return None to indicate file no longer exists
            except Exception as e:
                logging.error(f"Error deleting file from shared: {relative_path} - {str(e)}")
    
    # Handle case where file doesn't exist in either location
    if not mach3_exists and not shared_exists:
        return None
    
    # Get file info
    mach3_info = None
    shared_info = None
    
    if mach3_exists:
        try:
            mach3_hash = calculate_file_hash(mach3_path)
            mach3_info = {
                'mtime': os.path.getmtime(mach3_path),
                'hash': mach3_hash
            }
        except Exception as e:
            logging.error(f"Error getting Mach3 file info: {relative_path} - {str(e)}")
            mach3_info = {'mtime': 0, 'hash': None}
    
    if shared_exists:
        try:
            shared_hash = calculate_file_hash(shared_path)
            shared_info = {
                'mtime': os.path.getmtime(shared_path),
                'hash': shared_hash
            }
        except Exception as e:
            logging.error(f"Error getting shared file info: {relative_path} - {str(e)}")
            shared_info = {'mtime': 0, 'hash': None}
    
    # Compare and sync
    if mach3_exists and shared_exists:
        # Get previous hashes
        old_mach3_hash = prev_state.get('mach3_hash')
        old_shared_hash = prev_state.get('shared_hash')
        
        # Detect if either file has changed since last sync
        mach3_changed = old_mach3_hash != mach3_info['hash'] if old_mach3_hash else True
        shared_changed = old_shared_hash != shared_info['hash'] if old_shared_hash else True
        
        # Time difference between files
        time_diff = abs(mach3_info['mtime'] - shared_info['mtime'])
        
        logging.info(f"File analysis for {relative_path}:")
        logging.info(f"  Mach3 changed: {mach3_changed}, Shared changed: {shared_changed}")
        logging.info(f"  Time diff: {time_diff} seconds vs tolerance {TIME_TOLERANCE}")
        
        # Both changed - potential conflict
        if mach3_changed and shared_changed:
            logging.info(f"  CONFLICT: Both versions have changed")
            
            # If content is different
            if mach3_info['hash'] != shared_info['hash']:
                # If timestamps are similar, prefer Mach3 (primary)
                if time_diff <= TIME_TOLERANCE:
                    try:
                        shutil.copy2(mach3_path, shared_path)
                        logging.info(f"  RESOLVED: Used Mach3 version (close timestamps, Mach3 is primary)")
                    except Exception as e:
                        logging.error(f"  Error updating shared file: {str(e)}")
                else:
                    # Otherwise use the newer file
                    if mach3_info['mtime'] > shared_info['mtime']:
                        try:
                            shutil.copy2(mach3_path, shared_path)
                            logging.info(f"  RESOLVED: Used Mach3 version (newer)")
                        except Exception as e:
                            logging.error(f"  Error updating shared file: {str(e)}")
                    else:
                        try:
                            shutil.copy2(shared_path, mach3_path)
                            logging.info(f"  RESOLVED: Used shared version (newer)")
                        except Exception as e:
                            logging.error(f"  Error updating Mach3 file: {str(e)}")
        
        # Only Mach3 changed
        elif mach3_changed and mach3_info['hash'] != shared_info['hash']:
            try:
                shutil.copy2(mach3_path, shared_path)
                logging.info(f"  Updated in shared: Mach3 version changed")
            except Exception as e:
                logging.error(f"  Error updating shared file: {str(e)}")
        
        # Only shared changed
        elif shared_changed and mach3_info['hash'] != shared_info['hash']:
            try:
                shutil.copy2(shared_path, mach3_path)
                logging.info(f"  Updated in Mach3: shared version changed")
            except Exception as e:
                logging.error(f"  Error updating Mach3 file: {str(e)}")
        
        else:
            logging.info(f"  No changes needed for file")
        
        # Return current state
        return {
            'mach3_exists': True,
            'shared_exists': True,
            'mach3_mtime': mach3_info['mtime'],
            'shared_mtime': shared_info['mtime'],
            'mach3_hash': mach3_info['hash'],
            'shared_hash': shared_info['hash'],
            'last_sync': time.time()
        }
    
    # Only exists in Mach3, copy to shared
    elif mach3_exists:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(shared_path), exist_ok=True)
            
            shutil.copy2(mach3_path, shared_path)
            logging.info(f"  Copied to shared: {relative_path}")
            
            return {
                'mach3_exists': True,
                'shared_exists': True,
                'mach3_mtime': mach3_info['mtime'],
                'shared_mtime': os.path.getmtime(shared_path),
                'mach3_hash': mach3_info['hash'],
                'shared_hash': mach3_info['hash'],  # Just copied, so hash is the same
                'last_sync': time.time()
            }
        except Exception as e:
            logging.error(f"  Error copying to shared: {str(e)}")
            
            return {
                'mach3_exists': True,
                'shared_exists': False,
                'mach3_mtime': mach3_info['mtime'],
                'shared_mtime': 0,
                'mach3_hash': mach3_info['hash'],
                'shared_hash': None,
                'last_sync': time.time()
            }
    
    # Only exists in shared, copy to Mach3
    elif shared_exists:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(mach3_path), exist_ok=True)
            
            shutil.copy2(shared_path, mach3_path)
            logging.info(f"  Copied to Mach3: {relative_path}")
            
            return {
                'mach3_exists': True,
                'shared_exists': True,
                'mach3_mtime': os.path.getmtime(mach3_path),
                'shared_mtime': shared_info['mtime'],
                'mach3_hash': shared_info['hash'],  # Just copied, so hash is the same
                'shared_hash': shared_info['hash'],
                'last_sync': time.time()
            }
        except Exception as e:
            logging.error(f"  Error copying to Mach3: {str(e)}")
            
            return {
                'mach3_exists': False,
                'shared_exists': True,
                'mach3_mtime': 0,
                'shared_mtime': shared_info['mtime'],
                'mach3_hash': None,
                'shared_hash': shared_info['hash'],
                'last_sync': time.time()
            }

def sync_directory_structure(relative_dir):
    """
    Ensure directory structure exists in both locations.
    
    Args:
        relative_dir: Relative path to the directory
    """
    mach3_dir = os.path.join(MACH3_DIR, relative_dir)
    shared_dir = os.path.join(SHARED_DIR, relative_dir)
    
    try:
        # Create in Mach3 if it doesn't exist
        if not os.path.exists(mach3_dir):
            os.makedirs(mach3_dir, exist_ok=True)
            logging.info(f"Created directory in Mach3: {relative_dir}")
        
        # Create in shared if it doesn't exist
        if not os.path.exists(shared_dir):
            os.makedirs(shared_dir, exist_ok=True)
            logging.info(f"Created directory in shared: {relative_dir}")
            
        return True
    except Exception as e:
        logging.error(f"Error creating directory structure for {relative_dir}: {str(e)}")
        return False

def sync_individual_file(relative_path, sync_state):
    """
    Sync an individual file specified in FILES_TO_SYNC.
    
    Args:
        relative_path: Relative path to the file
        sync_state: Current sync state dictionary
        
    Returns:
        tuple: Updated sync state and whether sync was successful
    """
    mach3_path = os.path.join(MACH3_DIR, relative_path)
    shared_path = os.path.join(SHARED_DIR, relative_path)
    
    # Ensure parent directories exist
    os.makedirs(os.path.dirname(mach3_path), exist_ok=True)
    os.makedirs(os.path.dirname(shared_path), exist_ok=True)
    
    # Get previous state if it exists
    file_key = relative_path.replace('\\', '/')
    prev_state = sync_state['files'].get(file_key)
    
    # Sync the file
    new_state = sync_file(mach3_path, shared_path, relative_path, prev_state)
    
    # Update sync state
    if new_state:
        sync_state['files'][file_key] = new_state
    elif file_key in sync_state['files']:
        del sync_state['files'][file_key]
    
    return sync_state

def verify_sync_functionality():
    """
    Perform a quick verification of the sync functionality at startup.
    Creates a test file and verifies it gets synchronized.
    """
    try:
        test_file = os.path.join(MACH3_DIR, "DevelopmentEnvironment", ".sync_verification_test")
        shared_test_file = os.path.join(SHARED_DIR, "DevelopmentEnvironment", ".sync_verification_test")
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        os.makedirs(os.path.dirname(shared_test_file), exist_ok=True)
        
        # Create a test file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Creating sync verification file with timestamp: {timestamp}")
        
        with open(test_file, 'w') as f:
            f.write(f"Sync verification test - {timestamp}")
        
        # Sync this file immediately
        relative_path = os.path.relpath(test_file, MACH3_DIR)
        sync_state = load_sync_state()
        sync_state = sync_individual_file(relative_path, sync_state)
        save_sync_state(sync_state)
        
        # Check if file exists in shared folder
        if os.path.exists(shared_test_file):
            try:
                with open(shared_test_file, 'r') as f:
                    content = f.read()
                if timestamp in content:
                    logging.info("[SUCCESS] Sync verification successful!")
                else:
                    logging.warning("[WARNING]Sync verification partial - file exists but content doesn't match")
            except Exception as e:
                logging.warning(f"[WARNING] Sync verification error - couldn't read file: {str(e)}")
        else:
            logging.warning("[WARNING] Sync verification failed - test file not synced")
        
        # Clean up test files
        try:
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(shared_test_file):
                os.remove(shared_test_file)
        except Exception as e:
            logging.error(f"Error cleaning up test files: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error during sync verification: {str(e)}")
        logging.error(traceback.format_exc())

def sync_folder_contents(relative_folder, sync_state):
    """
    Sync all contents of a folder recursively.
    
    Args:
        relative_folder: Relative path to the folder
        sync_state: Current sync state dictionary
        
    Returns:
        dict: Updated sync state
    """
    logging.info(f"Syncing folder contents: {relative_folder}")
    
    mach3_folder = os.path.join(MACH3_DIR, relative_folder)
    shared_folder = os.path.join(SHARED_DIR, relative_folder)
    
    # Ensure directory structure exists
    if not sync_directory_structure(relative_folder):
        logging.error(f"Failed to create directory structure for {relative_folder}")
        return sync_state
    
    # Get current file lists
    mach3_files = get_all_files(mach3_folder, MACH3_DIR)
    shared_files = get_all_files(shared_folder, SHARED_DIR)
    
    # Track processed files to detect deletions
    processed_files = set()
    
    # First, sync all directory structures
    for rel_path in set(list(mach3_files.keys()) + list(shared_files.keys())):
        if rel_path not in processed_files:
            is_dir_in_mach3 = rel_path in mach3_files and mach3_files[rel_path].get('is_dir', False)
            is_dir_in_shared = rel_path in shared_files and shared_files[rel_path].get('is_dir', False)
            
            if is_dir_in_mach3 or is_dir_in_shared:
                sync_directory_structure(rel_path)
                processed_files.add(rel_path)
    
    # Update sync state with directories
    for rel_path in processed_files:
        if rel_path not in sync_state['folders']['mach3']:
            sync_state['folders']['mach3'][rel_path] = {'is_dir': True, 'mtime': time.time()}
        if rel_path not in sync_state['folders']['shared']:
            sync_state['folders']['shared'][rel_path] = {'is_dir': True, 'mtime': time.time()}
    
    # Detect deletions in mach3 folder
    for rel_path in list(sync_state['folders']['mach3'].keys()):
        # Skip if not under the current folder we're syncing
        if not rel_path.startswith(relative_folder):
            continue
            
        # If it was in mach3 but isn't anymore, and it exists in shared, delete from shared
        if rel_path not in mach3_files and rel_path in shared_files:
            shared_path = os.path.join(SHARED_DIR, rel_path)
            try:
                if sync_state['folders']['mach3'][rel_path].get('is_dir', False):
                    # It's a directory
                    if os.path.isdir(shared_path):
                        shutil.rmtree(shared_path)
                        logging.info(f"Deleted directory from shared (propagated): {rel_path}")
                else:
                    # It's a file
                    os.remove(shared_path)
                    logging.info(f"Deleted file from shared (propagated): {rel_path}")
                
                # Remove from sync state
                if rel_path in sync_state['folders']['mach3']:
                    del sync_state['folders']['mach3'][rel_path]
                if rel_path in sync_state['folders']['shared']:
                    del sync_state['folders']['shared'][rel_path]
            except Exception as e:
                logging.error(f"Error deleting from shared: {rel_path} - {str(e)}")
    
    # Detect deletions in shared folder
    for rel_path in list(sync_state['folders']['shared'].keys()):
        # Skip if not under the current folder we're syncing
        if not rel_path.startswith(relative_folder):
            continue
            
        # If it was in shared but isn't anymore, and it exists in mach3, delete from mach3
        if rel_path not in shared_files and rel_path in mach3_files:
            mach3_path = os.path.join(MACH3_DIR, rel_path)
            try:
                if sync_state['folders']['shared'][rel_path].get('is_dir', False):
                    # It's a directory
                    if os.path.isdir(mach3_path):
                        shutil.rmtree(mach3_path)
                        logging.info(f"Deleted directory from mach3 (propagated): {rel_path}")
                else:
                    # It's a file
                    os.remove(mach3_path)
                    logging.info(f"Deleted file from mach3 (propagated): {rel_path}")
                
                # Remove from sync state
                if rel_path in sync_state['folders']['mach3']:
                    del sync_state['folders']['mach3'][rel_path]
                if rel_path in sync_state['folders']['shared']:
                    del sync_state['folders']['shared'][rel_path]
            except Exception as e:
                logging.error(f"Error deleting from mach3: {rel_path} - {str(e)}")
    
    # Sync all files in both locations
    all_paths = set()
    all_paths.update([p for p, info in mach3_files.items() if not info.get('is_dir', False)])
    all_paths.update([p for p, info in shared_files.items() if not info.get('is_dir', False)])
    
    for rel_path in all_paths:
        # Skip if already processed or if it's a directory
        if rel_path in processed_files:
            continue
            
        # Make paths
        mach3_path = os.path.join(MACH3_DIR, rel_path)
        shared_path = os.path.join(SHARED_DIR, rel_path)
        
        # Get previous state if it exists
        file_key = rel_path.replace('\\', '/')
        prev_state = None
        if file_key in sync_state['folders']['mach3'] and file_key in sync_state['folders']['shared']:
            prev_state = {
                'mach3_exists': True,
                'shared_exists': True,
                'mach3_mtime': sync_state['folders']['mach3'][file_key].get('mtime', 0),
                'shared_mtime': sync_state['folders']['shared'][file_key].get('mtime', 0),
                'mach3_hash': sync_state['folders']['mach3'][file_key].get('hash'),
                'shared_hash': sync_state['folders']['shared'][file_key].get('hash')
            }
        
        # Sync the file
        new_state = sync_file(mach3_path, shared_path, rel_path, prev_state)
        
        # Update sync state
        if new_state:
            mach3_state = {
                'is_dir': False,
                'mtime': new_state['mach3_mtime'],
                'hash': new_state['mach3_hash']
            }
            shared_state = {
                'is_dir': False,
                'mtime': new_state['shared_mtime'],
                'hash': new_state['shared_hash']
            }
            sync_state['folders']['mach3'][file_key] = mach3_state
            sync_state['folders']['shared'][file_key] = shared_state
        else:
            # File was deleted or doesn't exist
            if file_key in sync_state['folders']['mach3']:
                del sync_state['folders']['mach3'][file_key]
            if file_key in sync_state['folders']['shared']:
                del sync_state['folders']['shared'][file_key]
        
        processed_files.add(rel_path)
    
    return sync_state

def run_sync():
    """
    Main sync function that runs the entire synchronization process.
    """
    try:
        sync_start_time = time.time()
        logging.info(f"========== Starting sync at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========")
        
        # Load sync state
        sync_state = load_sync_state()
        
        # Sync each folder
        for folder in FOLDERS_TO_SYNC:
            sync_state = sync_folder_contents(folder, sync_state)
            save_sync_state(sync_state)  # Save after each folder
        
        # Sync individual files
        for file_path in FILES_TO_SYNC:
            sync_state = sync_individual_file(file_path, sync_state)
        
        # Save final sync state
        save_sync_state(sync_state)
        
        sync_end_time = time.time()
        logging.info(f"Sync completed in {sync_end_time - sync_start_time:.2f} seconds")
        logging.info("==========================================================")
        
    except Exception as e:
        logging.error(f"Critical error in run_sync: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Try to send notification
        try:
            # Create an alert file
            with open(os.path.join(LOG_DIR, "sync_error_alert.txt"), "a") as alert_file:
                alert_file.write(f"{datetime.datetime.now().isoformat()}: Sync error: {str(e)}\n")
        except:
            pass

def check_directories():
    """Check if main directories exist and are accessible."""
    try:
        # Check Mach3 directory
        if not os.path.exists(MACH3_DIR):
            logging.error(f"Mach3 directory does not exist: {MACH3_DIR}")
            return False
        
        # Check shared directory
        if not os.path.exists(SHARED_DIR):
            logging.error(f"Shared directory does not exist: {SHARED_DIR}")
            return False
        
        # Check log directory
        if not os.path.exists(LOG_DIR):
            try:
                os.makedirs(LOG_DIR, exist_ok=True)
                logging.info(f"Created log directory: {LOG_DIR}")
            except Exception as e:
                logging.error(f"Cannot create log directory: {str(e)}")
                return False
        
        # Test write permissions
        test_file = os.path.join(LOG_DIR, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("Write test")
            os.remove(test_file)
        except Exception as e:
            logging.error(f"Cannot write to log directory: {str(e)}")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Error checking directories: {str(e)}")
        return False

def main():
    """Main function to start the sync script."""
    print(f"Mach3 Selective Sync starting from {SCRIPT_DIR}")
    print(f"Logs will be saved to {LOG_DIR}")
    
    try:
        logging.info("===============================================")
        logging.info("        Mach3 Selective Sync Starting         ")
        logging.info("===============================================")
        logging.info(f"Mach3 Directory: {MACH3_DIR}")
        logging.info(f"Shared Directory: {SHARED_DIR}")
        logging.info(f"Log Directory: {LOG_DIR}")
        logging.info(f"Sync State File: {SYNC_STATE_FILE}")
        logging.info(f"Folders to sync: {FOLDERS_TO_SYNC}")
        logging.info(f"Individual files to sync: {FILES_TO_SYNC}")
        
        # Check directories
        if not check_directories():
            logging.error("Directory check failed - exiting")
            return
        
        # Verify sync functionality
        verify_sync_functionality()
        
        # Initial sync
        run_sync()
        
        # Schedule sync to run every minute
        schedule.every(1).minutes.do(run_sync)
        
        logging.info("Sync scheduler started. Press Ctrl+C to stop.")
        print("Sync scheduler started. Press Ctrl+C to stop.")
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt. Shutting down.")
            print("Shutting down sync script...")
        
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
