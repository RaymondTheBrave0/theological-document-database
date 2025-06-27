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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io

def merge_pdfs(input_files, output_file, header_lines=0):
    """Merge multiple PDF files into one"""
    pdf_writer = PyPDF2.PdfWriter()
    
    def create_page_with_header_removed(page, header_lines=0):
        """Create a new page with header lines removed but keeping lesson title"""
        if header_lines <= 0:
            return page
            
        try:
            # Extract text from the page
            text = page.extract_text()
            lines = text.split('\n')
            
            # Remove the first N lines but preserve lesson title (typically 3rd line)
            # Skip first 2 lines (institute name, module info) but keep lesson title
            if len(lines) > header_lines and header_lines >= 2:
                # Keep lesson title (3rd line) and everything after header_lines
                lesson_title = lines[2] if len(lines) > 2 else ""
                remaining_content = lines[header_lines:]
                
                # Reconstruct content with lesson title at the top
                if lesson_title.strip() and "lesson" in lesson_title.lower():
                    new_lines = [lesson_title] + remaining_content
                else:
                    new_lines = remaining_content
                    
                new_text = '\n'.join(new_lines)
                
                # Create a new PDF page with the processed text
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                width, height = letter
                
                # Write text to new page
                y_position = height - 50
                for line in new_lines:
                    if line.strip():
                        can.drawString(50, y_position, line.strip()[:100])  # Limit line length
                        y_position -= 15
                        if y_position < 50:
                            break
                            
                can.save()
                packet.seek(0)
                
                # Create new PDF page
                new_pdf = PyPDF2.PdfReader(packet)
                return new_pdf.pages[0]
                
        except Exception as e:
            print(f"     Warning: Could not process header removal: {e}")
            
        return page
    
    print(f"Merging {len(input_files)} PDF files...")
    
    for i, file_path in enumerate(input_files, 1):
        print(f"  {i}. Adding {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Add all pages from this PDF
                pages_added = 0
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    
                    # Process page to remove header lines if requested
                    if header_lines > 0:
                        processed_page = create_page_with_header_removed(page, header_lines)
                        pdf_writer.add_page(processed_page)
                        print(f"     Added page {page_num + 1} (header lines removed)")
                    else:
                        pdf_writer.add_page(page)
                        
                    pages_added += 1
                    
                total_pages = len(pdf_reader.pages)
                if header_lines > 0:
                    print(f"     Added {pages_added}/{total_pages} pages (skipped {total_pages - pages_added} header-only pages)")
                else:
                    print(f"     Added {pages_added} pages")
                
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
    parser.add_argument('-hl', '--header-lines', type=int, default=0, help='Number of header lines to strip from each page')
    
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
    success = merge_pdfs(valid_files, args.output, args.header_lines)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
