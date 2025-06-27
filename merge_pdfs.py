#!/usr/bin/env python3
"""
PDF Merger Script
Merges multiple PDF files into a single PDF in sequence
"""

import os
import sys
import argparse
import re
from pathlib import Path
import PyPDF2

def merge_pdfs(input_files, output_file):
    """Merge multiple PDF files into one"""
    pdf_writer = PyPDF2.PdfWriter()
    
    print(f"Merging {len(input_files)} PDF files...")
    
    for i, file_path in enumerate(input_files, 1):
        print(f"  {i}. Adding {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Add all pages from this PDF
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                    
                print(f"     Added {len(pdf_reader.pages)} pages")
                
        except Exception as e:
            print(f"     ❌ Error processing {file_path}: {e}")
            continue
    
    # Write the merged PDF
    try:
        with open(output_file, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
        
        print(f"\n✅ Successfully merged into: {output_file}")
        print(f"📊 Total pages: {len(pdf_writer.pages)}")
        
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        return False
    
    return True

def natural_sort_key(text):
    """Generate sort key for natural numerical sorting"""
    # Split text into parts, converting numbers to integers
    def tryint(s):
        try:
            return int(s)
        except:
            return s
    return [tryint(c) for c in re.split('([0-9]+)', str(text))]

def get_pdf_files(directory, pattern="*.pdf", sort_method="natural"):
    """Get list of PDF files in directory with proper sorting"""
    path = Path(directory)
    pdf_files = list(path.glob(pattern))
    
    if sort_method == "natural":
        # Natural sorting (handles numbers properly: file1, file2, file10)
        pdf_files.sort(key=lambda x: natural_sort_key(x.name))
    elif sort_method == "alphabetical":
        # Standard alphabetical sorting
        pdf_files.sort(key=lambda x: x.name)
    elif sort_method == "modified":
        # Sort by modification time (oldest first)
        pdf_files.sort(key=lambda x: x.stat().st_mtime)
    
    return [str(f) for f in pdf_files]

def main():
    parser = argparse.ArgumentParser(description='Merge PDF files in sequence')
    parser.add_argument('files', nargs='*', help='PDF files to merge (in order)')
    parser.add_argument('-d', '--directory', help='Directory containing PDFs to merge')
    parser.add_argument('-o', '--output', default='merged_pdfs.pdf', help='Output filename')
    parser.add_argument('-p', '--pattern', default='*.pdf', help='File pattern (when using directory)')
    parser.add_argument('-s', '--sort', choices=['natural', 'alphabetical', 'modified'], 
                       default='natural', help='Sorting method (default: natural - handles numbers correctly)')
    
    args = parser.parse_args()
    
    # Determine input files and adjust output path
    if args.directory:
        print(f"📁 Looking for PDFs in: {args.directory}")
        print(f"🔤 Sorting method: {args.sort}")
        input_files = get_pdf_files(args.directory, args.pattern, args.sort)
        if not input_files:
            print("❌ No PDF files found in directory")
            return 1
        
        # If output file doesn't have a path, save it in the source directory
        if not os.path.dirname(args.output):
            args.output = os.path.join(args.directory, args.output)
            print(f"💾 Output will be saved in source directory: {args.output}")
            
    elif args.files:
        input_files = args.files
    else:
        print("❌ Please specify either files or directory")
        parser.print_help()
        return 1
    
    # Validate input files
    valid_files = []
    for file_path in input_files:
        if os.path.exists(file_path) and file_path.lower().endswith('.pdf'):
            valid_files.append(file_path)
        else:
            print(f"⚠️  Skipping invalid file: {file_path}")
    
    if not valid_files:
        print("❌ No valid PDF files to merge")
        return 1
    
    print(f"\n📋 Files to merge ({len(valid_files)}):")
    for i, file_path in enumerate(valid_files, 1):
        print(f"  {i}. {os.path.basename(file_path)}")
    
    # Merge PDFs
    success = merge_pdfs(valid_files, args.output)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
