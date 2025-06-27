"""
Database Manager for Document Database System
Handles vector database operations and metadata management
"""

import os
import sqlite3
import logging
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json
import ollama

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages both vector database and metadata operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vector_db_path = config['database']['vector_db_path']
        self.metadata_db_path = config['database']['metadata_db_path']
        self.embedding_model_name = config['embeddings']['model']
        self.similarity_threshold = config['embeddings']['similarity_threshold']
        self.batch_size = config['database']['batch_size']
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Initialize databases
        self._init_vector_database()
        self._init_metadata_database()
        
    def _init_embedding_model(self):
        """Initialize the embedding model (Ollama or sentence-transformers)"""
        embedding_provider = self.config['embeddings'].get('provider', 'sentence-transformers')
        
        if embedding_provider == 'ollama':
            try:
                # Test Ollama connection and model
                logger.info(f"Testing Ollama embedding model: {self.embedding_model_name}")
                test_response = ollama.embeddings(
                    model=self.embedding_model_name,
                    prompt="test"
                )
                logger.info(f"Successfully initialized Ollama embedding model: {self.embedding_model_name}")
                self.embedding_provider = 'ollama'
                return
            except Exception as e:
                logger.error(f"Failed to initialize Ollama embedding model: {e}")
                logger.info("Falling back to sentence-transformers...")
        
        # Fallback to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            device = self.config['embeddings']['device']
            if device == 'auto':
                device = 'cuda' if self.config['performance']['use_gpu'] else 'cpu'
            
            # Use a simple model name for sentence-transformers
            model_name = "all-MiniLM-L6-v2"
            logger.info(f"Initializing sentence-transformers model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name, device=device)
            self.embedding_provider = 'sentence-transformers'
            logger.info(f"Successfully initialized sentence-transformers model: {model_name} on {device}")
        except Exception as e:
            logger.error(f"Failed to initialize any embedding model: {e}")
            raise Exception("No embedding model could be initialized.")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using the configured provider"""
        try:
            if self.embedding_provider == 'ollama':
                response = ollama.embeddings(
                    model=self.embedding_model_name,
                    prompt=text
                )
                return response['embedding']
            else:  # sentence-transformers
                return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return a dummy embedding as fallback
            return [0.0] * 384  # Standard embedding dimension
    
    def _init_vector_database(self):
        """Initialize ChromaDB vector database"""
        try:
            # Create ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Initialized vector database at {self.vector_db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def _init_metadata_database(self):
        """Initialize SQLite metadata database"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.metadata_db_path), exist_ok=True)
            
            # Create tables
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT UNIQUE NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_date TIMESTAMP,
                    chunk_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'processed'
                )
            ''')
            
            # Document chunks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_index INTEGER,
                    chunk_text TEXT,
                    chunk_hash TEXT UNIQUE,
                    vector_id TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            ''')
            
            # Query history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    query_hash TEXT,
                    results_count INTEGER,
                    execution_time REAL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Initialized metadata database at {self.metadata_db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize metadata database: {e}")
            raise
    
    def calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {filepath}: {e}")
            return ""
    
    def calculate_text_hash(self, text: str) -> str:
        """Calculate SHA-256 hash of text content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def is_document_already_processed(self, filepath: str) -> bool:
        """Check if document is already in database"""
        try:
            file_hash = self.calculate_file_hash(filepath)
            if not file_hash:
                return False
                
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM documents WHERE file_hash = ?",
                (file_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking if document exists: {e}")
            return False
    
    def is_chunk_duplicate(self, chunk_text: str) -> bool:
        """Check if chunk content already exists in database"""
        try:
            chunk_hash = self.calculate_text_hash(chunk_text)
            
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM document_chunks WHERE chunk_hash = ?",
                (chunk_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking chunk duplication: {e}")
            return False
    
    def add_document(self, filepath: str, filename: str, file_type: str, 
                    chunks: List[str]) -> Optional[int]:
        """Add document and its chunks to the database"""
        try:
            # Check if already processed first
            if self.is_document_already_processed(filepath):
                logger.info(f"Document {filename} already exists in database")
                return None
                
            file_hash = self.calculate_file_hash(filepath)
            file_size = os.path.getsize(filepath)
            modified_date = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # Use timeout and WAL mode for better concurrency
            conn = sqlite3.connect(self.metadata_db_path, timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            # Insert document
            cursor.execute('''
                INSERT INTO documents 
                (filename, filepath, file_hash, file_size, file_type, modified_date, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (filename, filepath, file_hash, file_size, file_type, modified_date, len(chunks)))
            
            document_id = cursor.lastrowid
            
            # Process chunks in batches
            chunk_data = []
            embeddings = []
            vector_ids = []
            
            for i, chunk in enumerate(chunks):
                if self.is_chunk_duplicate(chunk):
                    # Skipping duplicate chunk
                    continue
                
                chunk_hash = self.calculate_text_hash(chunk)
                vector_id = f"doc_{document_id}_chunk_{i}"
                
                chunk_data.append((document_id, i, chunk, chunk_hash, vector_id))
                embeddings.append(self.generate_embedding(chunk))
                vector_ids.append(vector_id)
            
            if chunk_data:
                # Insert chunks into metadata database
                cursor.executemany('''
                    INSERT INTO document_chunks 
                    (document_id, chunk_index, chunk_text, chunk_hash, vector_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', chunk_data)
                
                # Insert embeddings into vector database
                self.collection.add(
                    embeddings=embeddings,
                    documents=[item[2] for item in chunk_data],  # chunk_text
                    ids=vector_ids,
                    metadatas=[{
                        "document_id": item[0],
                        "chunk_index": item[1],
                        "filename": filename,
                        "filepath": filepath
                    } for item in chunk_data]
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added document {filename}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to add document {filename}: {e}")
            return None
    
    def search_similar_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            for i in range(len(results['documents'][0])):
                search_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'vector_id': results['ids'][0][i]
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_similar_documents_filtered(self, query: str, document_ids: List[int], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents within a filtered set of document IDs"""
        try:
            # Generate embedding for the query
            embedding = self.embedding_model.encode(query)
            
            # Get chunk IDs for the specified documents
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Build placeholders for the IN clause
            placeholders = ','.join('?' * len(document_ids))
            cursor.execute(f'''
                SELECT vector_id FROM document_chunks 
                WHERE document_id IN ({placeholders})
            ''', document_ids)
            
            allowed_chunk_ids = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            
            if not allowed_chunk_ids:
                logger.warning("No chunks found for the specified document IDs")
                return []
            
            # Perform vector search with filtering by IDs
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, len(allowed_chunk_ids)),
                ids=allowed_chunk_ids,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    similarity = 1 - distance  # Convert distance to similarity
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity': similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            return []
    
    def get_document_info(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document information by ID"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, filepath, file_type, file_size, 
                       created_date, modified_date, chunk_count, status
                FROM documents WHERE id = ?
            ''', (document_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'filename': result[1],
                    'filepath': result[2],
                    'file_type': result[3],
                    'file_size': result[4],
                    'created_date': result[5],
                    'modified_date': result[6],
                    'chunk_count': result[7],
                    'status': result[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Get document count
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            # Get chunk count
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            chunk_count = cursor.fetchone()[0]
            
            # Get total file size
            cursor.execute("SELECT SUM(file_size) FROM documents")
            total_size = cursor.fetchone()[0] or 0
            
            # Get file type distribution
            cursor.execute('''
                SELECT file_type, COUNT(*) 
                FROM documents 
                GROUP BY file_type
            ''')
            file_types = dict(cursor.fetchall())
            
            conn.close()
            
            # Get vector database stats
            vector_count = self.collection.count()
            
            return {
                'document_count': doc_count,
                'chunk_count': chunk_count,
                'vector_count': vector_count,
                'total_file_size': total_size,
                'file_type_distribution': file_types
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def save_query_history(self, query: str, results_count: int, execution_time: float):
        """Save query to history"""
        try:
            query_hash = self.calculate_text_hash(query)
            
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO query_history 
                (query_text, query_hash, results_count, execution_time)
                VALUES (?, ?, ?, ?)
            ''', (query, query_hash, results_count, execution_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save query history: {e}")
    
    def cleanup_database(self):
        """Cleanup and optimize database"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            # Remove orphaned chunks
            cursor.execute('''
                DELETE FROM document_chunks 
                WHERE document_id NOT IN (SELECT id FROM documents)
            ''')
            
            # Vacuum database
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            logger.info("Database cleanup completed")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
