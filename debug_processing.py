#!/usr/bin/env python3

import os
import sys
import logging
import sqlite3
import pdfplumber

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_database_status(file_path):
    """Check if file is already in database"""
    conn = sqlite3.connect('./data/metadata.db')
    cursor = conn.execute('SELECT filename FROM documents WHERE filename = ?', (os.path.basename(file_path),))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"✓ File '{os.path.basename(file_path)}' IS in database")
        return True
    else:
        print(f"✗ File '{os.path.basename(file_path)}' is NOT in database")
        return False

def test_processing_pipeline(file_path):
    """Test the complete processing pipeline for a single file"""
    
    print(f"=== DEBUGGING PROCESSING PIPELINE ===")
    print(f"File: {file_path}")
    print(f"Exists: {os.path.exists(file_path)}")
    print(f"Size: {os.path.getsize(file_path)} bytes")
    
    # Check database status
    check_database_status(file_path)
    
    # Test supported format check
    SUPPORTED_FORMATS = ['.txt', '.pdf', '.doc', '.docx', '.csv', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    is_supported = any(file_path.endswith(ext) for ext in SUPPORTED_FORMATS)
    print(f"Supported format: {is_supported}")
    
    # Test text extraction
    print(f"\n=== TEXT EXTRACTION TEST ===")
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
        
        print(f"Extracted text length: {len(text)} characters")
        print(f"Has content: {bool(text.strip())}")
        
        if text.strip():
            print(f"Sample (first 100 chars): {text.strip()[:100]}")
            
            # Test chunking
            words = text.split()
            print(f"Word count: {len(words)}")
            
            # Simulate chunking (default chunk size)
            max_chunk_size = 1000
            chunk_overlap = 100
            chunks = []
            for start in range(0, len(words), max_chunk_size - chunk_overlap):
                end = start + max_chunk_size
                chunk = " ".join(words[start:end])
                chunks.append(chunk)
            
            print(f"Generated chunks: {len(chunks)}")
            print(f"First chunk length: {len(chunks[0]) if chunks else 0} characters")
            
            return text, chunks
        else:
            print("ERROR: No text extracted!")
            return None, None
            
    except Exception as e:
        print(f"ERROR during text extraction: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def simulate_add_to_database(file_path, filename, chunks):
    """Simulate adding to database to see if there are any issues"""
    print(f"\n=== DATABASE SIMULATION ===")
    
    try:
        conn = sqlite3.connect('./data/metadata.db')
        
        # Check if already exists
        cursor = conn.execute('SELECT id FROM documents WHERE filename = ?', (filename,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"File already exists in database with ID: {existing[0]}")
            conn.close()
            return False
        
        print(f"File not in database - would be added with {len(chunks)} chunks")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database simulation error: {e}")
        return False

if __name__ == "__main__":
    test_files = [
        "./data/documents/Apostolic Gifts.pdf",
        "./data/documents/Conditional Security versus Unconditional Eternal Security.pdf",
        "./data/documents/The Apostolic Preaching.pdf"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            text, chunks = test_processing_pipeline(file_path)
            if chunks:
                simulate_add_to_database(file_path, os.path.basename(file_path), chunks)
        else:
            print(f"File not found: {file_path}")
