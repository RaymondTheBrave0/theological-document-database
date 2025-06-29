#!/usr/bin/env python3
"""
Bible Verse Fetcher
Fetch and display Bible verses using the ESV API
"""

import requests
import sys
import json
from pathlib import Path

# ESV API Configuration
ESV_API_KEY = "170fa0e450e67f5ee7be4c40b3c3005858a92392"
ESV_API_BASE = "https://api.esv.org/v3"

def get_verse_text(reference):
    """Fetch verse text from ESV API"""
    try:
        headers = {
            'Authorization': f'Token {ESV_API_KEY}'
        }
        
        params = {
            'q': reference,
            'include-headings': False,
            'include-footnotes': False,
            'include-verse-numbers': True,
            'include-short-copyright': False,
            'include-passage-references': True
        }
        
        response = requests.get(f'{ESV_API_BASE}/passage/text/', 
                              headers=headers, 
                              params=params,
                              timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('passages') and len(data['passages']) > 0:
                passage = data['passages'][0].strip()
                # Clean up the text
                passage = passage.replace('\n\n', '\n').strip()
                return {
                    'success': True,
                    'text': passage,
                    'reference': reference
                }
            else:
                return {
                    'success': False,
                    'error': f'No text found for "{reference}"'
                }
        else:
            return {
                'success': False,
                'error': f'API Error: {response.status_code} - {response.text}'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def display_verse(verse_data):
    """Display verse in a formatted way"""
    if verse_data['success']:
        print("\n" + "="*60)
        print(f"📖 {verse_data['reference']}")
        print("="*60)
        print(verse_data['text'])
        print("="*60)
        print("ESV - English Standard Version")
        print()
    else:
        print(f"❌ Error: {verse_data['error']}")

def interactive_mode():
    """Interactive mode for verse lookup"""
    print("🔍 Bible Verse Lookup Tool")
    print("Type 'quit' or 'exit' to stop")
    print("Examples: 'John 3:16', 'Genesis 1:1', 'Psalm 23'")
    print()
    
    while True:
        try:
            reference = input("Enter scripture reference: ").strip()
            
            if reference.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not reference:
                continue
                
            print("🔄 Fetching verse...")
            verse_data = get_verse_text(reference)
            display_verse(verse_data)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode - reference provided as argument
        reference = ' '.join(sys.argv[1:])
        print(f"🔄 Fetching {reference}...")
        verse_data = get_verse_text(reference)
        display_verse(verse_data)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
