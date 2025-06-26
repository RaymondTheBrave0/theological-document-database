"""
Scripture Reference Indexer
Extracts and indexes Bible scripture references from documents with flexible format support
"""

import os
import sqlite3
import logging
import re
import json
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ScriptureIndexer:
    """Extracts and indexes Bible scripture references from documents"""
    
    def __init__(self, metadata_db_path: str):
        self.metadata_db_path = metadata_db_path
        self.book_patterns = self._load_book_patterns()
        self._init_scripture_index_table()
    
    def _load_book_patterns(self) -> Dict[str, List[str]]:
        """Load comprehensive Bible book name patterns and abbreviations"""
        return {
            # Old Testament
            'Genesis': ['genesis', 'gen', 'ge', 'gn'],
            'Exodus': ['exodus', 'exod', 'exo', 'ex'],
            'Leviticus': ['leviticus', 'lev', 'le', 'lv'],
            'Numbers': ['numbers', 'num', 'nu', 'nm', 'nb'],
            'Deuteronomy': ['deuteronomy', 'deut', 'deu', 'dt'],
            'Joshua': ['joshua', 'josh', 'jos', 'jsh'],
            'Judges': ['judges', 'judg', 'jdg', 'jg', 'jgs'],
            'Ruth': ['ruth', 'rut', 'rt'],
            '1 Samuel': ['1 samuel', '1samuel', '1 sam', '1sam', '1 sa', '1sa', 'i samuel', 'i sam'],
            '2 Samuel': ['2 samuel', '2samuel', '2 sam', '2sam', '2 sa', '2sa', 'ii samuel', 'ii sam'],
            '1 Kings': ['1 kings', '1kings', '1 kgs', '1kgs', '1 ki', '1ki', 'i kings', 'i kgs'],
            '2 Kings': ['2 kings', '2kings', '2 kgs', '2kgs', '2 ki', '2ki', 'ii kings', 'ii kgs'],
            '1 Chronicles': ['1 chronicles', '1chronicles', '1 chron', '1chron', '1 chr', '1chr', 'i chronicles'],
            '2 Chronicles': ['2 chronicles', '2chronicles', '2 chron', '2chron', '2 chr', '2chr', 'ii chronicles'],
            'Ezra': ['ezra', 'ezr', 'ez'],
            'Nehemiah': ['nehemiah', 'neh', 'ne'],
            'Esther': ['esther', 'esth', 'est', 'es'],
            'Job': ['job', 'jb'],
            'Psalms': ['psalms', 'psalm', 'pss', 'ps', 'psa', 'psm', 'pslm'],
            'Proverbs': ['proverbs', 'prov', 'pro', 'prv', 'pr'],
            'Ecclesiastes': ['ecclesiastes', 'eccl', 'ecc', 'ec', 'qoh'],
            'Song of Solomon': ['song of solomon', 'song', 'canticles', 'canticle of canticles', 'sos', 'so', 'ca'],
            'Isaiah': ['isaiah', 'isa', 'is'],
            'Jeremiah': ['jeremiah', 'jer', 'je', 'jr'],
            'Lamentations': ['lamentations', 'lam', 'la'],
            'Ezekiel': ['ezekiel', 'ezek', 'eze', 'ezk'],
            'Daniel': ['daniel', 'dan', 'da', 'dn'],
            'Hosea': ['hosea', 'hos', 'ho'],
            'Joel': ['joel', 'joe', 'jl'],
            'Amos': ['amos', 'amo', 'am'],
            'Obadiah': ['obadiah', 'obad', 'ob'],
            'Jonah': ['jonah', 'jnh', 'jon'],
            'Micah': ['micah', 'mic', 'mc'],
            'Nahum': ['nahum', 'nah', 'na'],
            'Habakkuk': ['habakkuk', 'hab', 'hb'],
            'Zephaniah': ['zephaniah', 'zeph', 'zep', 'zp'],
            'Haggai': ['haggai', 'hag', 'hg'],
            'Zechariah': ['zechariah', 'zech', 'zec', 'zc'],
            'Malachi': ['malachi', 'mal', 'ml'],
            
            # New Testament
            'Matthew': ['matthew', 'matt', 'mat', 'mt'],
            'Mark': ['mark', 'mar', 'mrk', 'mk'],
            'Luke': ['luke', 'luk', 'lk'],
            'John': ['john', 'joh', 'jhn', 'jn'],
            'Acts': ['acts', 'act', 'ac'],
            'Romans': ['romans', 'rom', 'ro', 'rm'],
            '1 Corinthians': ['1 corinthians', '1corinthians', '1 cor', '1cor', '1 co', '1co', 'i corinthians', 'i cor'],
            '2 Corinthians': ['2 corinthians', '2corinthians', '2 cor', '2cor', '2 co', '2co', 'ii corinthians', 'ii cor'],
            'Galatians': ['galatians', 'gal', 'ga'],
            'Ephesians': ['ephesians', 'eph', 'ep'],
            'Philippians': ['philippians', 'phil', 'php', 'pp'],
            'Colossians': ['colossians', 'col', 'co'],
            '1 Thessalonians': ['1 thessalonians', '1thessalonians', '1 thess', '1thess', '1 th', '1th', 'i thessalonians'],
            '2 Thessalonians': ['2 thessalonians', '2thessalonians', '2 thess', '2thess', '2 th', '2th', 'ii thessalonians'],
            '1 Timothy': ['1 timothy', '1timothy', '1 tim', '1tim', '1 ti', '1ti', 'i timothy', 'i tim'],
            '2 Timothy': ['2 timothy', '2timothy', '2 tim', '2tim', '2 ti', '2ti', 'ii timothy', 'ii tim'],
            'Titus': ['titus', 'tit', 'ti'],
            'Philemon': ['philemon', 'phlm', 'phm', 'pm'],
            'Hebrews': ['hebrews', 'heb', 'he'],
            'James': ['james', 'jas', 'jm'],
            '1 Peter': ['1 peter', '1peter', '1 pet', '1pet', '1 pe', '1pe', 'i peter', 'i pet'],
            '2 Peter': ['2 peter', '2peter', '2 pet', '2pet', '2 pe', '2pe', 'ii peter', 'ii pet'],
            '1 John': ['1 john', '1john', '1 joh', '1joh', '1 jn', '1jn', 'i john', 'i joh'],
            '2 John': ['2 john', '2john', '2 joh', '2joh', '2 jn', '2jn', 'ii john', 'ii joh'],
            '3 John': ['3 john', '3john', '3 joh', '3joh', '3 jn', '3jn', 'iii john', 'iii joh'],
            'Jude': ['jude', 'jud', 'jd'],
            'Revelation': ['revelation', 'rev', 'rv', 're']
        }
    
    def _init_scripture_index_table(self):
        """Initialize the scripture index table"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Create scripture index table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scripture_index (
                    reference TEXT NOT NULL,
                    document_id INTEGER NOT NULL,
                    context_snippets TEXT,
                    normalized_reference TEXT,
                    PRIMARY KEY (reference, document_id),
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scripture_lookup 
                ON scripture_index (reference)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_normalized_scripture 
                ON scripture_index (normalized_reference)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_document_scriptures 
                ON scripture_index (document_id)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Initialized scripture index table")
            
        except Exception as e:
            logger.error(f"Failed to initialize scripture index table: {e}")
            raise
    
    def _build_scripture_patterns(self) -> List[str]:
        """Build comprehensive regex patterns for scripture references"""
        patterns = []
        
        # Create pattern for each book and its abbreviations
        for book_name, abbreviations in self.book_patterns.items():
            for abbrev in abbreviations:
                # Escape special regex characters
                escaped_abbrev = re.escape(abbrev)
                
                # Various patterns for different formats:
                # 1. "John 3:16" or "Jn 3:16"
                patterns.append(rf'\b{escaped_abbrev}\.?\s+\d+:\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*\b')
                
                # 2. "John 3 16" or "Jn 3 16" (space instead of colon)
                patterns.append(rf'\b{escaped_abbrev}\.?\s+\d+\s+\d+(?:-\d+)?\b')
                
                # 3. "John chapter 3 verse 16"
                patterns.append(rf'\b{escaped_abbrev}\.?\s+(?:chapter\s+)?\d+(?:\s+verse\s+|\s+v\.?\s+)\d+(?:-\d+)?\b')
                
                # 4. "John 3:16-20" (verse ranges)
                patterns.append(rf'\b{escaped_abbrev}\.?\s+\d+:\d+-\d+\b')
                
                # 5. "John 3:16, 20" (multiple verses)
                patterns.append(rf'\b{escaped_abbrev}\.?\s+\d+:\d+(?:,\s*\d+)*\b')
                
                # 6. "John 3:16-20, 25" (mixed ranges and individual verses)
                patterns.append(rf'\b{escaped_abbrev}\.?\s+\d+:\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*\b')
        
        return patterns
    
    def extract_scripture_references(self, text: str) -> Dict[str, Dict]:
        """Extract scripture references from text with context"""
        scripture_data = {}
        patterns = self._build_scripture_patterns()
        
        # Split text into sentences for context
        sentences = re.split(r'[.!?]+', text)
        
        # Search for all patterns
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in matches:
                reference = match.group().strip()
                normalized_ref = self._normalize_reference(reference)
                
                if normalized_ref:
                    # Find context sentences
                    context_snippets = []
                    match_pos = match.start()
                    
                    # Find sentences containing this reference
                    for sentence in sentences:
                        if reference.lower() in sentence.lower():
                            context_snippets.append(sentence.strip())
                    
                    # Store or update reference data
                    if normalized_ref not in scripture_data:
                        scripture_data[normalized_ref] = {
                            'original_reference': reference,
                            'context_snippets': [],
                            'count': 0
                        }
                    
                    scripture_data[normalized_ref]['count'] += 1
                    scripture_data[normalized_ref]['context_snippets'].extend(context_snippets[:2])
        
        # Deduplicate and limit context snippets
        for ref_data in scripture_data.values():
            ref_data['context_snippets'] = list(set(ref_data['context_snippets']))[:3]
        
        return scripture_data
    
    def _normalize_reference(self, reference: str) -> Optional[str]:
        """Normalize scripture reference to standard format"""
        try:
            # Clean up the reference
            ref = re.sub(r'[,.]$', '', reference.strip())
            
            # Find the book name
            for book_name, abbreviations in self.book_patterns.items():
                for abbrev in abbreviations:
                    pattern = rf'\b{re.escape(abbrev)}\.?\s*'
                    if re.match(pattern, ref, re.IGNORECASE):
                        # Extract chapter and verse
                        remainder = re.sub(pattern, '', ref, flags=re.IGNORECASE).strip()
                        
                        # Handle different formats
                        if ':' in remainder:
                            # "3:16" format
                            return f"{book_name} {remainder}"
                        elif ' ' in remainder:
                            # "3 16" format - convert to "3:16"
                            parts = remainder.split()
                            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                                return f"{book_name} {parts[0]}:{parts[1]}"
                        elif remainder.isdigit():
                            # Just chapter number
                            return f"{book_name} {remainder}"
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to normalize reference '{reference}': {e}")
            return None
    
    def index_document_scriptures(self, document_id: int, document_content: str, filename: str = None) -> bool:
        """Index scripture references for a single document"""
        try:
            # Extract scripture references
            scriptures = self.extract_scripture_references(document_content)
            
            # Use filename for logging if provided, otherwise fall back to document_id
            display_name = filename if filename else f"document {document_id}"
            
            if not scriptures:
                logger.info(f"No scripture references found in {display_name}")
                return True
            
            # Store in database
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Clear existing scripture references for this document
            cursor.execute(
                "DELETE FROM scripture_index WHERE document_id = ?",
                (document_id,)
            )
            
            # Insert new scripture references
            for normalized_ref, data in scriptures.items():
                context_json = json.dumps(data['context_snippets'])
                cursor.execute('''
                    INSERT INTO scripture_index 
                    (reference, document_id, context_snippets, normalized_reference)
                    VALUES (?, ?, ?, ?)
                ''', (data['original_reference'], document_id, context_json, normalized_ref))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Indexed {len(scriptures)} scripture references for {display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index scriptures for {display_name}: {e}")
            return False
    
    def search_by_scripture(self, scripture_query: str) -> List[Dict]:
        """Search for documents containing specific scripture references"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Normalize the query
            normalized_query = self._normalize_reference(scripture_query)
            
            # Search by both original and normalized references
            # If normalization failed (returns None), still search in both fields
            if normalized_query:
                cursor.execute('''
                    SELECT si.document_id, d.filename, d.filepath, 
                           si.reference, si.normalized_reference, si.context_snippets
                    FROM scripture_index si
                    JOIN documents d ON si.document_id = d.id
                    WHERE si.reference LIKE ? OR si.normalized_reference LIKE ?
                    ORDER BY d.filename
                ''', (f'%{scripture_query}%', f'%{normalized_query}%'))
            else:
                # If normalization failed, search only in the original fields
                cursor.execute('''
                    SELECT si.document_id, d.filename, d.filepath, 
                           si.reference, si.normalized_reference, si.context_snippets
                    FROM scripture_index si
                    JOIN documents d ON si.document_id = d.id
                    WHERE si.reference LIKE ? OR si.normalized_reference LIKE ?
                    ORDER BY d.filename
                ''', (f'%{scripture_query}%', f'%{scripture_query}%'))
            
            results = cursor.fetchall()
            conn.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'document_id': row[0],
                    'filename': row[1],
                    'filepath': row[2],
                    'reference': row[3],
                    'normalized_reference': row[4],
                    'context_snippets': json.loads(row[5]) if row[5] else []
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search by scripture: {e}")
            return []
    
    def get_document_scriptures(self, document_id: int) -> List[Dict]:
        """Get all scripture references for a specific document"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT reference, normalized_reference, context_snippets
                FROM scripture_index
                WHERE document_id = ?
                ORDER BY normalized_reference
            ''', (document_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            scriptures = []
            for row in results:
                scriptures.append({
                    'reference': row[0],
                    'normalized_reference': row[1],
                    'context_snippets': json.loads(row[2]) if row[2] else []
                })
            
            return scriptures
            
        except Exception as e:
            logger.error(f"Failed to get scriptures for document {document_id}: {e}")
            return []
    
    def get_scripture_statistics(self) -> Dict:
        """Get statistics about scripture references in the database"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Total scripture references
            cursor.execute("SELECT COUNT(*) FROM scripture_index")
            total_references = cursor.fetchone()[0]
            
            # Unique normalized references
            cursor.execute("SELECT COUNT(DISTINCT normalized_reference) FROM scripture_index")
            unique_references = cursor.fetchone()[0]
            
            # Top scripture references
            cursor.execute('''
                SELECT normalized_reference, COUNT(*) as doc_count
                FROM scripture_index
                GROUP BY normalized_reference
                ORDER BY doc_count DESC
                LIMIT 20
            ''')
            top_scriptures = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_references': total_references,
                'unique_references': unique_references,
                'top_scriptures': [
                    {'reference': row[0], 'document_count': row[1]}
                    for row in top_scriptures
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get scripture statistics: {e}")
            return {}
    
    def rebuild_scripture_index_for_all_documents(self) -> bool:
        """Rebuild the scripture index for all documents using document chunks"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Get all documents with filename
            cursor.execute("SELECT id, filename FROM documents")
            documents = cursor.fetchall()
            
            success_count = 0
            total_count = len(documents)
            
            logger.info(f"Starting to rebuild scripture index for {total_count} documents...")
            
            for doc_id, filename in documents:
                try:
                    # Get all chunks for this document
                    cursor.execute(
                        "SELECT chunk_text FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
                        (doc_id,)
                    )
                    chunks = cursor.fetchall()
                    
                    if chunks:
                        # Combine all chunks for this document
                        combined_content = "\n\n".join([chunk[0] for chunk in chunks])
                        
                        # Index the document using the extracted text content with filename for better logging
                        if self.index_document_scriptures(doc_id, combined_content, filename):
                            success_count += 1
                    else:
                        logger.warning(f"No chunks found for {filename or f'document {doc_id}'}")
                        
                except Exception as e:
                    logger.error(f"Failed to process {filename or f'document {doc_id}'}: {e}")
                    
            conn.close()
            
            logger.info(f"Rebuilt scripture index for {success_count}/{total_count} documents")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to rebuild scripture index: {e}")
            return False
