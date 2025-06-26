"""
Bible Scripture Reference Extractor and Lookup System
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class BibleLookup:
    """Extract and lookup Bible references from text"""
    
    def __init__(self):
        self.bible_books = self._load_bible_books()
        self.scripture_cache = {}
        
    def _load_bible_books(self) -> Dict[str, str]:
        """Load Bible book names and abbreviations"""
        return {
            # Old Testament
            'genesis': 'Genesis', 'gen': 'Genesis', 'ge': 'Genesis',
            'exodus': 'Exodus', 'exod': 'Exodus', 'ex': 'Exodus',
            'leviticus': 'Leviticus', 'lev': 'Leviticus', 'le': 'Leviticus',
            'numbers': 'Numbers', 'num': 'Numbers', 'nu': 'Numbers',
            'deuteronomy': 'Deuteronomy', 'deut': 'Deuteronomy', 'dt': 'Deuteronomy',
            'joshua': 'Joshua', 'josh': 'Joshua', 'jos': 'Joshua',
            'judges': 'Judges', 'judg': 'Judges', 'jg': 'Judges',
            'ruth': 'Ruth', 'ru': 'Ruth',
            '1 samuel': '1 Samuel', '1sam': '1 Samuel', '1sa': '1 Samuel',
            '2 samuel': '2 Samuel', '2sam': '2 Samuel', '2sa': '2 Samuel',
            '1 kings': '1 Kings', '1kgs': '1 Kings', '1ki': '1 Kings',
            '2 kings': '2 Kings', '2kgs': '2 Kings', '2ki': '2 Kings',
            '1 chronicles': '1 Chronicles', '1chr': '1 Chronicles', '1ch': '1 Chronicles',
            '2 chronicles': '2 Chronicles', '2chr': '2 Chronicles', '2ch': '2 Chronicles',
            'ezra': 'Ezra', 'ezr': 'Ezra',
            'nehemiah': 'Nehemiah', 'neh': 'Nehemiah', 'ne': 'Nehemiah',
            'esther': 'Esther', 'est': 'Esther', 'es': 'Esther',
            'job': 'Job', 'jb': 'Job',
            'psalms': 'Psalms', 'psalm': 'Psalms', 'ps': 'Psalms', 'psa': 'Psalms',
            'proverbs': 'Proverbs', 'prov': 'Proverbs', 'pr': 'Proverbs',
            'ecclesiastes': 'Ecclesiastes', 'eccl': 'Ecclesiastes', 'ec': 'Ecclesiastes',
            'song of solomon': 'Song of Solomon', 'song': 'Song of Solomon', 'ss': 'Song of Solomon',
            'isaiah': 'Isaiah', 'isa': 'Isaiah', 'is': 'Isaiah',
            'jeremiah': 'Jeremiah', 'jer': 'Jeremiah', 'je': 'Jeremiah',
            'lamentations': 'Lamentations', 'lam': 'Lamentations', 'la': 'Lamentations',
            'ezekiel': 'Ezekiel', 'ezek': 'Ezekiel', 'eze': 'Ezekiel',
            'daniel': 'Daniel', 'dan': 'Daniel', 'da': 'Daniel',
            'hosea': 'Hosea', 'hos': 'Hosea', 'ho': 'Hosea',
            'joel': 'Joel', 'joe': 'Joel',
            'amos': 'Amos', 'am': 'Amos',
            'obadiah': 'Obadiah', 'obad': 'Obadiah', 'ob': 'Obadiah',
            'jonah': 'Jonah', 'jon': 'Jonah',
            'micah': 'Micah', 'mic': 'Micah', 'mi': 'Micah',
            'nahum': 'Nahum', 'nah': 'Nahum', 'na': 'Nahum',
            'habakkuk': 'Habakkuk', 'hab': 'Habakkuk', 'hb': 'Habakkuk',
            'zephaniah': 'Zephaniah', 'zeph': 'Zephaniah', 'zep': 'Zephaniah',
            'haggai': 'Haggai', 'hag': 'Haggai', 'hg': 'Haggai',
            'zechariah': 'Zechariah', 'zech': 'Zechariah', 'zec': 'Zechariah',
            'malachi': 'Malachi', 'mal': 'Malachi', 'ml': 'Malachi',
            
            # New Testament
            'matthew': 'Matthew', 'matt': 'Matthew', 'mt': 'Matthew',
            'mark': 'Mark', 'mk': 'Mark',
            'luke': 'Luke', 'lk': 'Luke', 'lu': 'Luke',
            'john': 'John', 'jn': 'John', 'joh': 'John',
            'acts': 'Acts', 'ac': 'Acts',
            'romans': 'Romans', 'rom': 'Romans', 'ro': 'Romans',
            '1 corinthians': '1 Corinthians', '1cor': '1 Corinthians', '1co': '1 Corinthians',
            '2 corinthians': '2 Corinthians', '2cor': '2 Corinthians', '2co': '2 Corinthians',
            'galatians': 'Galatians', 'gal': 'Galatians', 'ga': 'Galatians',
            'ephesians': 'Ephesians', 'eph': 'Ephesians', 'ep': 'Ephesians',
            'philippians': 'Philippians', 'phil': 'Philippians', 'php': 'Philippians',
            'colossians': 'Colossians', 'col': 'Colossians',
            '1 thessalonians': '1 Thessalonians', '1thess': '1 Thessalonians', '1th': '1 Thessalonians',
            '2 thessalonians': '2 Thessalonians', '2thess': '2 Thessalonians', '2th': '2 Thessalonians',
            '1 timothy': '1 Timothy', '1tim': '1 Timothy', '1ti': '1 Timothy',
            '2 timothy': '2 Timothy', '2tim': '2 Timothy', '2ti': '2 Timothy',
            'titus': 'Titus', 'tit': 'Titus', 'ti': 'Titus',
            'philemon': 'Philemon', 'phlm': 'Philemon', 'phm': 'Philemon',
            'hebrews': 'Hebrews', 'heb': 'Hebrews', 'he': 'Hebrews',
            'james': 'James', 'jas': 'James', 'jm': 'James',
            '1 peter': '1 Peter', '1pet': '1 Peter', '1pe': '1 Peter',
            '2 peter': '2 Peter', '2pet': '2 Peter', '2pe': '2 Peter',
            '1 john': '1 John', '1jn': '1 John', '1jo': '1 John',
            '2 john': '2 John', '2jn': '2 John', '2jo': '2 John',
            '3 john': '3 John', '3jn': '3 John', '3jo': '3 John',
            'jude': 'Jude', 'jud': 'Jude',
            'revelation': 'Revelation', 'rev': 'Revelation', 're': 'Revelation'
        }
    
    def extract_bible_references(self, text: str) -> List[Dict[str, str]]:
        """Extract Bible references from text"""
        references = []
        
        # Pattern to match Bible references like "John 3:16", "1 Cor 13:4-7", etc.
        patterns = [
            # Full book names with chapter:verse
            r'\\b(?:1|2|3)\\s*(?:' + '|'.join(self.bible_books.keys()) + r')\\s+\\d+:\\d+(?:-\\d+)?\\b',
            # Abbreviated book names
            r'\\b(?:' + '|'.join([k for k in self.bible_books.keys() if len(k) <= 4]) + r')\\s+\\d+:\\d+(?:-\\d+)?\\b',
            # Just book and chapter
            r'\\b(?:1|2|3)\\s*(?:' + '|'.join(self.bible_books.keys()) + r')\\s+\\d+\\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref_text = match.group().strip()
                parsed_ref = self._parse_reference(ref_text)
                if parsed_ref and parsed_ref not in references:
                    references.append(parsed_ref)
        
        return references
    
    def _parse_reference(self, ref_text: str) -> Optional[Dict[str, str]]:
        """Parse a Bible reference string"""
        try:
            # Remove extra whitespace and normalize
            ref_text = re.sub(r'\\s+', ' ', ref_text.strip())
            
            # Extract book, chapter, and verse
            # Handle patterns like "John 3:16", "1 Cor 13:4-7", "Romans 8"
            match = re.match(r'^(\\d*\\s*\\w+(?:\\s+\\w+)*)\\s+(\\d+)(?::(\\d+)(?:-(\\d+))?)?', ref_text, re.IGNORECASE)
            
            if not match:
                return None
            
            book_text = match.group(1).strip().lower()
            chapter = match.group(2)
            start_verse = match.group(3)
            end_verse = match.group(4)
            
            # Normalize book name
            book = self.bible_books.get(book_text)
            if not book:
                # Try partial matches
                for key, value in self.bible_books.items():
                    if key in book_text or book_text in key:
                        book = value
                        break
            
            if not book:
                return None
            
            # Format the reference
            if start_verse:
                if end_verse:
                    reference = f"{book} {chapter}:{start_verse}-{end_verse}"
                else:
                    reference = f"{book} {chapter}:{start_verse}"
            else:
                reference = f"{book} {chapter}"
            
            return {
                'reference': reference,
                'book': book,
                'chapter': int(chapter),
                'start_verse': int(start_verse) if start_verse else None,
                'end_verse': int(end_verse) if end_verse else None,
                'original_text': ref_text
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse Bible reference '{ref_text}': {e}")
            return None
    
    def get_scripture_text(self, reference: Dict[str, str]) -> Optional[str]:
        """Get the actual scripture text (placeholder - would connect to Bible API)"""
        # This is a placeholder implementation
        # In a real system, you would connect to a Bible API like:
        # - Bible Gateway API
        # - ESV API
        # - YouVersion API
        # - Local Bible database
        
        ref_key = reference['reference']
        
        # Sample verses for common references (you would replace this with real API calls)
        sample_verses = {
            'John 3:16': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
            'Romans 8:28': 'And we know that in all things God works for the good of those who love him, who have been called according to his purpose.',
            'Philippians 4:13': 'I can do all this through him who gives me strength.',
            'Psalm 23:1': 'The Lord is my shepherd, I lack nothing.',
            'Matthew 28:19': 'Therefore go and make disciples of all nations, baptizing them in the name of the Father and of the Son and of the Holy Spirit.',
            'Romans 3:23': 'for all have sinned and fall short of the glory of God,',
            'Ephesians 2:8-9': 'For it is by grace you have been saved, through faith—and this is not from yourselves, it is the gift of God— not by works, so that no one can boast.'
        }
        
        return sample_verses.get(ref_key, f"[Scripture text for {ref_key} would be retrieved from Bible API]")
    
    def enhance_text_with_scripture(self, text: str) -> str:
        """Enhance text by adding scripture references and their content"""
        references = self.extract_bible_references(text)
        
        if not references:
            return text
        
        enhanced_text = text
        scripture_additions = []
        
        for ref in references:
            scripture_text = self.get_scripture_text(ref)
            if scripture_text:
                scripture_additions.append(f"\\n\\n**{ref['reference']}**: \"{scripture_text}\"")
        
        if scripture_additions:
            enhanced_text += "\\n\\n--- Bible References ---" + "".join(scripture_additions)
        
        return enhanced_text
