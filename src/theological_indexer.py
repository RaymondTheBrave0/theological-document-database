"""
Theological Concept Indexer
Extracts and indexes theological concepts from documents for efficient retrieval
"""

import os
import sqlite3
import logging
import re
import yaml
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TheologicalIndexer:
    """Extracts and indexes theological concepts from documents"""
    
    def __init__(self, metadata_db_path: str):
        self.metadata_db_path = metadata_db_path
        self.theological_concepts = self._load_theological_concepts()
        self._init_theological_index_table()
    
    def _load_theological_concepts(self) -> Set[str]:
        """Load theological concepts from YAML configuration file"""
        try:
            # Look for theological_concepts.yaml in the project root
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'theological_concepts.yaml')
            
            if not os.path.exists(config_path):
                logger.warning(f"Theological concepts config not found at {config_path}, using minimal defaults")
                return {'god', 'jesus', 'christ', 'lord', 'bible', 'scripture', 'word'}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Extract all concepts from all categories
            all_concepts = set()
            theological_concepts = config.get('theological_concepts', {})
            
            for category, concepts in theological_concepts.items():
                if isinstance(concepts, list):
                    all_concepts.update(concepts)
            
            # Store config options for later use
            self.config = config.get('config', {})
            
            logger.info(f"Loaded {len(all_concepts)} theological concepts from configuration file")
            return all_concepts
            
        except Exception as e:
            logger.error(f"Failed to load theological concepts from config: {e}")
            # Fallback to minimal set
            return {'god', 'jesus', 'christ', 'lord', 'bible', 'scripture', 'word'}
    
    def _init_theological_index_table(self):
        """Initialize the theological concept index table"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Create theological concept index table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS theological_concept_index (
                    concept TEXT NOT NULL,
                    document_id INTEGER NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    context_snippets TEXT,
                    PRIMARY KEY (concept, document_id),
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_concept_lookup 
                ON theological_concept_index (concept)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_document_concepts 
                ON theological_concept_index (document_id)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Initialized theological concept index table")
            
        except Exception as e:
            logger.error(f"Failed to initialize theological index table: {e}")
            raise
    
    def extract_concepts_from_text(self, text: str) -> Dict[str, Dict]:
        """Extract theological concepts from text with context"""
        concept_data = {}
        
        # Get case sensitivity setting from config
        case_sensitive = self.config.get('case_sensitive', False)
        search_text = text if case_sensitive else text.lower()
        
        # Split text into sentences for context extraction
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]  # Remove empty sentences
        
        for concept in self.theological_concepts:
            # Prepare concept for matching based on case sensitivity
            search_concept = concept if case_sensitive else concept.lower()
            
            # Find all occurrences of the concept
            pattern = r'\b' + re.escape(search_concept) + r'\b'
            matches = list(re.finditer(pattern, search_text, re.IGNORECASE if not case_sensitive else 0))
            
            if matches:
                frequency = len(matches)
                context_snippets = []
                
                # Extract context for each match by finding sentences that contain the concept
                for match in matches[:5]:  # Limit to first 5 contexts
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Find the sentence containing this match
                    for sentence in sentences:
                        sentence_lower = sentence.lower() if not case_sensitive else sentence
                        if search_concept in sentence_lower:
                            # Avoid duplicate context snippets
                            if sentence.strip() not in context_snippets:
                                context_snippets.append(sentence.strip())
                            if len(context_snippets) >= 3:  # Limit to 3 unique contexts
                                break
                
                concept_data[concept] = {
                    'frequency': frequency,
                    'context_snippets': context_snippets[:3]  # Keep top 3 contexts
                }
        
        return concept_data
    
    def index_document(self, document_id: int, document_content: str, filename: str = None) -> bool:
        """Index a single document for theological concepts"""
        try:
            # Extract concepts from document
            concepts = self.extract_concepts_from_text(document_content)
            
            # Use filename for logging if provided, otherwise fall back to document_id
            display_name = filename if filename else f"document {document_id}"
            
            if not concepts:
                logger.info(f"No theological concepts found in {display_name}")
                return True
            
            # Store in database
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Clear existing concepts for this document
            cursor.execute(
                "DELETE FROM theological_concept_index WHERE document_id = ?",
                (document_id,)
            )
            
            # Insert new concepts
            for concept, data in concepts.items():
                context_json = json.dumps(data['context_snippets'])
                cursor.execute('''
                    INSERT INTO theological_concept_index 
                    (concept, document_id, frequency, context_snippets)
                    VALUES (?, ?, ?, ?)
                ''', (concept, document_id, data['frequency'], context_json))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Indexed {len(concepts)} concepts for {display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index {display_name}: {e}")
            return False
    
    def search_by_concepts(self, concepts: List[str], min_frequency: int = 1) -> List[Dict]:
        """Search for documents containing specific theological concepts"""
        try:
            if not concepts:
                return []
                
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Build query for multiple concepts
            concept_placeholders = ','.join('?' * len(concepts))
            
            query = f'''
                SELECT tci.document_id, d.filename, d.filepath, 
                       tci.concept, tci.frequency, tci.context_snippets,
                       COUNT(*) as concept_matches
                FROM theological_concept_index tci
                JOIN documents d ON tci.document_id = d.id
                WHERE tci.concept IN ({concept_placeholders})
                AND tci.frequency >= ?
                GROUP BY tci.document_id, d.filename, d.filepath
                ORDER BY concept_matches DESC, tci.frequency DESC
            '''
            
            cursor.execute(query, concepts + [min_frequency])
            results = cursor.fetchall()
            conn.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'document_id': row[0],
                    'filename': row[1],
                    'filepath': row[2],
                    'concept_matches': row[6],
                    'total_frequency': row[4]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search by concepts: {e}")
            return []
    
    def get_document_concepts(self, document_id: int) -> List[Dict]:
        """Get all theological concepts for a specific document"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT concept, frequency, context_snippets
                FROM theological_concept_index
                WHERE document_id = ?
                ORDER BY frequency DESC
            ''', (document_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            concepts = []
            for row in results:
                concepts.append({
                    'concept': row[0],
                    'frequency': row[1],
                    'context_snippets': json.loads(row[2]) if row[2] else []
                })
            
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to get concepts for document {document_id}: {e}")
            return []
    
    def get_concept_statistics(self) -> Dict:
        """Get statistics about theological concepts in the database"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Total concepts
            cursor.execute("SELECT COUNT(*) FROM theological_concept_index")
            total_entries = cursor.fetchone()[0]
            
            # Unique concepts
            cursor.execute("SELECT COUNT(DISTINCT concept) FROM theological_concept_index")
            unique_concepts = cursor.fetchone()[0]
            
            # Top concepts
            cursor.execute('''
                SELECT concept, COUNT(*) as doc_count, SUM(frequency) as total_freq
                FROM theological_concept_index
                GROUP BY concept
                ORDER BY doc_count DESC, total_freq DESC
                LIMIT 20
            ''')
            top_concepts = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'unique_concepts': unique_concepts,
                'top_concepts': [
                    {'concept': row[0], 'document_count': row[1], 'total_frequency': row[2]}
                    for row in top_concepts
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get concept statistics: {e}")
            return {}
    
    def rebuild_index_for_all_documents(self) -> bool:
        """Rebuild the theological concept index for all documents"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Get all documents with filename
            cursor.execute("SELECT id, filepath, filename FROM documents")
            documents = cursor.fetchall()
            
            success_count = 0
            total_count = len(documents)
            
            logger.info(f"Starting to rebuild index for {total_count} documents...")
            
            for doc_id, filepath, filename in documents:
                try:
                    # Read document content from chunks table
                    cursor.execute(
                        "SELECT chunk_text FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
                        (doc_id,)
                    )
                    chunks = cursor.fetchall()
                    
                    if chunks:
                        # Combine all chunks into full document content
                        content = '\n'.join(chunk[0] for chunk in chunks if chunk[0])
                        
                        # Index the document with filename for better logging
                        if self.index_document(doc_id, content, filename):
                            success_count += 1
                    else:
                        logger.warning(f"No chunks found for document: {filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to process document {filename or doc_id}: {e}")
            
            conn.close()
            logger.info(f"Rebuilt index for {success_count}/{total_count} documents")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return False
