#!/usr/bin/env python3
"""
Test Document Preprocessing
Tests the document preprocessor with various scripture reference formats
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.document_preprocessor import DocumentPreprocessor

def test_preprocessing():
    """Test the document preprocessor functionality"""
    
    # Initialize preprocessor
    preprocessor = DocumentPreprocessor()
    
    # Test cases for scripture normalization
    test_texts = [
        "This references Mal_3:16 in the text.",
        "See also Gen_1:1 and Exod_20:3-4.",
        "The verse john 3:16 is famous.",
        "Check 1cor. 13:4-7 for love description.",
        "Read I John 4:8 and II Peter 1:21.",
        "Matt. 5 : 44 says to love enemies.",
        "In romans  8:28 we see god's plan.",
        "jesus christ is mentioned in phil 2:5-11.",
        "The holy spirit guides us (acts 1:8).",
        "Study rev. 21:4 about heaven.",
    ]
    
    print("Testing Scripture Reference Normalization:")
    print("=" * 60)
    
    for i, text in enumerate(test_texts, 1):
        processed = preprocessor.preprocess_document(text)
        print(f"{i}. Original:  {text}")
        print(f"   Processed: {processed}")
        print()
    
    # Test theological term corrections
    theological_test = """
    In this text we see that god loves us and jesus died for our sins.
    The holy spirit guides believers and christ is our savior.
    moses led israel and paul wrote many letters.
    The bible teaches about salvation and grace.
    """
    
    print("Testing Theological Term Corrections:")
    print("=" * 60)
    print("Original text:")
    print(theological_test)
    print("\nProcessed text:")
    processed_theological = preprocessor.preprocess_document(theological_test)
    print(processed_theological)

if __name__ == "__main__":
    test_preprocessing()
