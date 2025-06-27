#!/usr/bin/env python3
"""
Process All Footnotes
Batch processes all Word documents in a directory to inline footnotes/endnotes
"""

import os
import sys
import glob
from pathlib import Path
from inline_footnotes import inline_manual_notes

def process_all_documents(directory_path: str):
    """Process all .docx files in a directory"""
    
    # Find all .docx files (excluding backups and already processed files)
    pattern = os.path.join(directory_path, "*.docx")
    all_files = glob.glob(pattern)
    
    # Filter out backup files and already inlined files
    files_to_process = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        if not filename.endswith('.backup') and '_inlined' not in filename:
            files_to_process.append(file_path)
    
    if not files_to_process:
        print("No documents found to process")
        return
    
    print(f"Found {len(files_to_process)} documents to process:")
    for file_path in files_to_process:
        print(f"  - {os.path.basename(file_path)}")
    
    print("\nProcessing documents...")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        print(f"\nProcessing: {filename}")
        
        try:
            success = inline_manual_notes(file_path)
            if success:
                success_count += 1
                print(f"✓ Successfully processed: {filename}")
            else:
                error_count += 1
                print(f"✗ Failed to process: {filename}")
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing {filename}: {e}")
    
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total files: {len(files_to_process)}")
    
    if success_count > 0:
        print(f"\nProcessed files saved with '_inlined' suffix")
        print("Original files backed up with '.backup' suffix")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 process_all_footnotes.py <directory_path>")
        print("Example: python3 process_all_footnotes.py data/documents")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
        sys.exit(1)
    
    if not os.path.isdir(directory_path):
        print(f"Path is not a directory: {directory_path}")
        sys.exit(1)
    
    process_all_documents(directory_path)

if __name__ == "__main__":
    main()
