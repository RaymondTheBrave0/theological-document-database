"""
Document Preprocessor
Normalizes scripture references and corrects theological concept spelling
"""

import re
import os
import yaml
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentPreprocessor:
    """Preprocesses documents for consistent indexing"""

    def __init__(self, theological_corrections: Dict[str, str] = None):
        self.theological_corrections = theological_corrections or self._get_default_theological_corrections()
        self.book_name_mappings = self._get_book_name_mappings()
        
    def _get_book_name_mappings(self) -> Dict[str, str]:
        """Get mapping of abbreviated book names to full names"""
        return {
            # Old Testament
            'gen': 'Genesis', 'ge': 'Genesis', 'gn': 'Genesis',
            'exod': 'Exodus', 'exo': 'Exodus', 'ex': 'Exodus',
            'lev': 'Leviticus', 'le': 'Leviticus', 'lv': 'Leviticus',
            'num': 'Numbers', 'nu': 'Numbers', 'nm': 'Numbers', 'nb': 'Numbers',
            'deut': 'Deuteronomy', 'deu': 'Deuteronomy', 'dt': 'Deuteronomy',
            'josh': 'Joshua', 'jos': 'Joshua', 'jsh': 'Joshua',
            'judg': 'Judges', 'jdg': 'Judges', 'jg': 'Judges', 'jgs': 'Judges',
            'rut': 'Ruth', 'rt': 'Ruth',
            '1sam': '1 Samuel', '1sa': '1 Samuel', 'isam': '1 Samuel',
            '2sam': '2 Samuel', '2sa': '2 Samuel', 'iisam': '2 Samuel',
            '1kgs': '1 Kings', '1ki': '1 Kings', 'ikgs': '1 Kings',
            '2kgs': '2 Kings', '2ki': '2 Kings', 'iikgs': '2 Kings',
            '1chr': '1 Chronicles', '1chron': '1 Chronicles', 'ichr': '1 Chronicles',
            '2chr': '2 Chronicles', '2chron': '2 Chronicles', 'iichr': '2 Chronicles',
            'ezr': 'Ezra', 'ez': 'Ezra',
            'neh': 'Nehemiah', 'ne': 'Nehemiah',
            'esth': 'Esther', 'est': 'Esther', 'es': 'Esther',
            'jb': 'Job',
            'pss': 'Psalms', 'ps': 'Psalms', 'psa': 'Psalms', 'psm': 'Psalms', 'pslm': 'Psalms',
            'prov': 'Proverbs', 'pro': 'Proverbs', 'prv': 'Proverbs', 'pr': 'Proverbs',
            'eccl': 'Ecclesiastes', 'ecc': 'Ecclesiastes', 'ec': 'Ecclesiastes', 'qoh': 'Ecclesiastes',
            'song': 'Song of Solomon', 'sos': 'Song of Solomon', 'so': 'Song of Solomon', 'ca': 'Song of Solomon',
            'isa': 'Isaiah',
            'jer': 'Jeremiah', 'je': 'Jeremiah', 'jr': 'Jeremiah',
            'lam': 'Lamentations', 'la': 'Lamentations',
            'ezek': 'Ezekiel', 'eze': 'Ezekiel', 'ezk': 'Ezekiel',
            'dan': 'Daniel', 'da': 'Daniel', 'dn': 'Daniel',
            'hos': 'Hosea', 'ho': 'Hosea',
            'joe': 'Joel', 'jl': 'Joel',
            'amo': 'Amos', 'am': 'Amos',
            'obad': 'Obadiah', 'ob': 'Obadiah',
            'jnh': 'Jonah', 'jon': 'Jonah',
            'mic': 'Micah', 'mc': 'Micah',
            'nah': 'Nahum', 'na': 'Nahum',
            'hab': 'Habakkuk', 'hb': 'Habakkuk',
            'zeph': 'Zephaniah', 'zep': 'Zephaniah', 'zp': 'Zephaniah',
            'hag': 'Haggai', 'hg': 'Haggai',
            'zech': 'Zechariah', 'zec': 'Zechariah', 'zc': 'Zechariah',
            'mal': 'Malachi', 'ml': 'Malachi',
            
            # New Testament
            'matt': 'Matthew', 'mat': 'Matthew', 'mt': 'Matthew',
            'mar': 'Mark', 'mrk': 'Mark', 'mk': 'Mark',
            'luk': 'Luke', 'lk': 'Luke',
            'joh': 'John', 'jhn': 'John', 'jn': 'John',
            'act': 'Acts', 'ac': 'Acts',
            'rom': 'Romans', 'ro': 'Romans', 'rm': 'Romans',
            '1cor': '1 Corinthians', '1co': '1 Corinthians', 'icor': '1 Corinthians',
            '2cor': '2 Corinthians', '2co': '2 Corinthians', 'iicor': '2 Corinthians',
            'gal': 'Galatians', 'ga': 'Galatians',
            'eph': 'Ephesians', 'ep': 'Ephesians',
            'phil': 'Philippians', 'php': 'Philippians', 'pp': 'Philippians',
            'col': 'Colossians', 'co': 'Colossians',
            '1thess': '1 Thessalonians', '1th': '1 Thessalonians', 'ithess': '1 Thessalonians',
            '2thess': '2 Thessalonians', '2th': '2 Thessalonians', 'iithess': '2 Thessalonians',
            '1tim': '1 Timothy', '1ti': '1 Timothy', 'itim': '1 Timothy',
            '2tim': '2 Timothy', '2ti': '2 Timothy', 'iitim': '2 Timothy',
            'tit': 'Titus', 'ti': 'Titus',
            'phlm': 'Philemon', 'phm': 'Philemon', 'pm': 'Philemon',
            'heb': 'Hebrews', 'he': 'Hebrews',
            'jas': 'James', 'jm': 'James',
            '1pet': '1 Peter', '1pe': '1 Peter', 'ipet': '1 Peter',
            '2pet': '2 Peter', '2pe': '2 Peter', 'iipet': '2 Peter',
            '1joh': '1 John', '1jn': '1 John', 'ijoh': '1 John',
            '2joh': '2 John', '2jn': '2 John', 'iijoh': '2 John',
            '3joh': '3 John', '3jn': '3 John', 'iiijoh': '3 John',
            'jud': 'Jude', 'jd': 'Jude',
            'rev': 'Revelation', 'rv': 'Revelation', 're': 'Revelation'
        }

    def normalize_scripture_references(self, text: str) -> str:
        """Convert all formats of scripture references to a consistent style"""
        # First, handle underscore separators (e.g., Mal_3:16)
        text = re.sub(r'([a-zA-Z]+)_+(\d+):(\d+)', r'\1 \2:\3', text)
        
        # Handle various punctuation and spacing issues
        patterns = [
            # Remove extra periods in abbreviations: "Matt." -> "Matt"
            (r'\b([a-zA-Z]+)\.+(\s*\d+)', r'\1 \2'),
            # Normalize spacing around colons: "3 : 16" -> "3:16"
            (r'(\d+)\s*:\s*(\d+)', r'\1:\2'),
            # Handle multiple spaces: "1  John" -> "1 John"
            (r'\b(\d+)\s+(\w+)', r'\1 \2'),
            # Handle roman numerals: "I John" -> "1 John", "II John" -> "2 John"
            (r'\bI\s+([a-zA-Z]+)', r'1 \1'),
            (r'\bII\s+([a-zA-Z]+)', r'2 \1'),
            (r'\bIII\s+([a-zA-Z]+)', r'3 \1'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        # Expand abbreviated book names to full names (only when followed by numbers)
        for abbrev, full_name in self.book_name_mappings.items():
            # Only replace if followed by chapter/verse pattern (with optional period and flexible spacing)
            pattern = rf'\b{re.escape(abbrev)}\.?(?=\s+\d+[:\s]?\d+)'
            text = re.sub(pattern, full_name, text, flags=re.IGNORECASE)
            # Also handle case where book name is followed by just chapter number
            pattern2 = rf'\b{re.escape(abbrev)}\.?(?=\s+\d+\s)'
            text = re.sub(pattern2, full_name, text, flags=re.IGNORECASE)
        
        return text

    def _get_default_theological_corrections(self) -> Dict[str, str]:
        """Get default theological term corrections"""
        return {
            # Basic theological terms
            'god': 'God',
            'jesus': 'Jesus', 
            'christ': 'Christ',
            'lord': 'Lord',
            'holy spirit': 'Holy Spirit',
            'spirit': 'Spirit',
            'father': 'Father',
            'son': 'Son',
            
            # Biblical names and places
            'yahweh': 'Yahweh',
            'jehovah': 'Jehovah',
            'moses': 'Moses',
            'abraham': 'Abraham',
            'david': 'David',
            'paul': 'Paul',
            'peter': 'Peter',
            'israel': 'Israel',
            'jerusalem': 'Jerusalem',
            
            # Common theological concepts
            'salvation': 'salvation',
            'redemption': 'redemption',
            'grace': 'grace',
            'mercy': 'mercy',
            'righteousness': 'righteousness',
            'faith': 'faith',
            'love': 'love',
            'sin': 'sin',
            'forgiveness': 'forgiveness',
            'eternal life': 'eternal life',
            'kingdom of god': 'kingdom of God',
            'gospel': 'gospel',
            'trinity': 'Trinity',
            'incarnation': 'incarnation',
            'resurrection': 'resurrection',
            'crucifixion': 'crucifixion',
            'atonement': 'atonement',
            'justification': 'justification',
            'sanctification': 'sanctification',
            'glorification': 'glorification',
            
            # Church and ministry terms
            'church': 'church',
            'pastor': 'pastor',
            'minister': 'minister',
            'priest': 'priest',
            'deacon': 'deacon',
            'elder': 'elder',
            'apostle': 'apostle',
            'disciple': 'disciple',
            'prophet': 'prophet',
            
            # Scripture and Bible terms
            'bible': 'Bible',
            'scripture': 'Scripture',
            'word of god': 'Word of God',
            'old testament': 'Old Testament',
            'new testament': 'New Testament',
            'gospel': 'Gospel',
            'psalm': 'Psalm',
            'proverb': 'Proverb',
            
            # Worship and practice terms
            'prayer': 'prayer',
            'worship': 'worship',
            'praise': 'praise',
            'thanksgiving': 'thanksgiving',
            'communion': 'communion',
            'baptism': 'baptism',
            'eucharist': 'Eucharist',
            'sacrament': 'sacrament'
        }

    def correct_theological_terms(self, text: str) -> str:
        """Corrects common theological concept misspellings"""
        for term, correct_term in self.theological_corrections.items():
            pattern = rf'\b{re.escape(term)}\b'
            text = re.sub(pattern, correct_term, text, flags=re.IGNORECASE)
        
        return text

    def preprocess_document(self, text: str) -> str:
        """Complete preprocessing for a document"""
        text = self.normalize_scripture_references(text)
        text = self.correct_theological_terms(text)
        return text


def get_theological_corrections() -> Dict[str, str]:
    """Loads common theological term corrections"""
    return {
        'god': 'God',
        'jesus': 'Jesus',
        'christ': 'Christ',
        'holy spirit': 'Holy Spirit',
        'yahweh': 'Yahweh'
        # Add more corrections as needed
    }

# Example usage
if __name__ == "__main__":
    sample_text = "This is a sample text with Mal_3:16 and jesus."
    processor = DocumentPreprocessor(get_theological_corrections())
    processed_text = processor.preprocess_document(sample_text)
    print(processed_text)

