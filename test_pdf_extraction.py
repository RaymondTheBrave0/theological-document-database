#!/usr/bin/env python3

import pdfplumber
import sys
import traceback

def test_pdf_extraction(file_path):
    """Test PDF text extraction for debugging"""
    print(f"Testing PDF extraction for: {file_path}")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Number of pages: {len(pdf.pages)}")
            
            total_text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                total_text += page_text
                print(f"Page {i+1}: {len(page_text)} characters")
                
                # Show first 100 chars of each page as sample
                if page_text.strip():
                    sample = page_text.strip()[:100].replace('\n', ' ')
                    print(f"  Sample: {sample}...")
                else:
                    print(f"  Sample: [NO TEXT EXTRACTED]")
            
            print(f"\nTotal extracted text: {len(total_text)} characters")
            print(f"Has meaningful content: {bool(total_text.strip())}")
            
            if total_text.strip():
                # Show first 200 characters
                sample = total_text.strip()[:200].replace('\n', ' ')
                print(f"First 200 chars: {sample}...")
                return True
            else:
                print("ERROR: No text could be extracted from this PDF")
                return False
                
    except Exception as e:
        print(f"ERROR extracting from PDF: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    file_path = "./data/documents/Apostolic Gifts.pdf"
    success = test_pdf_extraction(file_path)
    
    if not success:
        print("\n=== DIAGNOSIS ===")
        print("This PDF may be:")
        print("1. Image-based (scanned document requiring OCR)")
        print("2. Password protected")
        print("3. Corrupted or malformed")
        print("4. Using unsupported text encoding")
        
        # Try alternate extraction method
        print("\nTrying alternate extraction with PyPDF2...")
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"PyPDF2 detected {len(pdf_reader.pages)} pages")
                
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    print(f"Page {i+1}: {len(page_text)} characters")
                    if page_text.strip():
                        sample = page_text.strip()[:100].replace('\n', ' ')
                        print(f"  Sample: {sample}...")
                        break
        except Exception as e2:
            print(f"PyPDF2 also failed: {e2}")
