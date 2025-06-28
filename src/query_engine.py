"""
Query Engine for Document Database System
Integrates vector search with Ollama for contextual responses
"""

import time
import logging
import ollama
from typing import List, Dict, Any, Optional
from .database_manager import DatabaseManager
from .bible_lookup import BibleLookup
from .scripture_indexer import ScriptureIndexer
from .theological_indexer import TheologicalIndexer

logger = logging.getLogger(__name__)

class QueryEngine:
    """Handles queries by combining vector search with Ollama-generated responses"""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.ollama_config = config['ollama']
        self.max_results = config['output']['max_results']
        self.include_sources = config['output']['include_sources']
        
        # Initialize Bible lookup system
        self.bible_lookup = BibleLookup()
        
        # Initialize Scripture indexer
        try:
            self.scripture_indexer = ScriptureIndexer(self.db_manager.metadata_db_path)
        except Exception as e:
            logger.warning(f"Failed to initialize scripture indexer: {e}")
            self.scripture_indexer = None
        
        # Initialize Theological indexer
        try:
            self.theological_indexer = TheologicalIndexer(self.db_manager.metadata_db_path)
        except Exception as e:
            logger.warning(f"Failed to initialize theological indexer: {e}")
            self.theological_indexer = None
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test connection to Ollama service"""
        try:
            # Try to connect and check if the model exists
            response = ollama.list()
            
            # Handle both dict response and object response
            if hasattr(response, 'models'):
                models = response.models
            elif isinstance(response, dict) and 'models' in response:
                models = response['models']
            else:
                logger.warning("Unexpected response format from Ollama")
                return
            
            # Extract model names - handle both dict and object formats
            model_names = []
            for model in models:
                if hasattr(model, 'model'):
                    model_names.append(model.model)
                elif isinstance(model, dict) and 'name' in model:
                    model_names.append(model['name'])
                elif isinstance(model, dict) and 'model' in model:
                    model_names.append(model['model'])
            
            if self.ollama_config['model'] not in model_names:
                logger.warning(f"Model {self.ollama_config['model']} not found. Available models: {model_names}")
                if model_names:
                    # Use the first available model
                    self.ollama_config['model'] = model_names[0]
                    logger.info(f"Using model: {self.ollama_config['model']}")
                else:
                    logger.error("No models available in Ollama")
            else:
                logger.info(f"Using Ollama model: {self.ollama_config['model']}")
                    
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            logger.info("Queries will use vector search only")
    
    def query(self, query_text: str, use_llm: bool = True, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a query using vector search and optionally Ollama
        
        Args:
            query_text: The user's query
            use_llm: Whether to use Ollama for response generation
            top_k: Number of top results to retrieve
        
        Returns:
            Dictionary containing search results and generated response
        """
        start_time = time.time()
        
        if top_k is None:
            top_k = self.max_results
        
        # Perform vector search
        search_results = self.db_manager.search_similar_documents(query_text, top_k=top_k)
        
        response_data = {
            'query': query_text,
            'search_results': search_results,
            'llm_response': None,
            'execution_time': 0,
            'sources_used': []
        }
        
        if search_results and use_llm:
            try:
                # Generate contextual response using Ollama
                llm_response = self._generate_llm_response(query_text, search_results)
                response_data['llm_response'] = llm_response
                
                # Extract sources used
                if self.include_sources:
                    response_data['sources_used'] = self._extract_sources(search_results)
                    
            except Exception as e:
                logger.error(f"LLM response generation failed: {e}")
                response_data['llm_response'] = "Error generating LLM response. Vector search results available."
        
        execution_time = time.time() - start_time
        response_data['execution_time'] = execution_time
        
        # Save query to history
        self.db_manager.save_query_history(
            query_text, 
            len(search_results), 
            execution_time
        )
        
        return response_data
    
    def _generate_llm_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate a response using Ollama based on search results"""
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5]):  # Use top 5 results for context
            filename = result['metadata']['filename']
            content = result['content']
            similarity = result['similarity']
            
            # Use filename as the document identifier instead of just numbers
            context_parts.append(f"Document \"{filename}\" (relevance: {similarity:.3f}):\n{content}\n")
        
        context = "\n".join(context_parts)
        
        # Enhance context with Bible references if found
        enhanced_context_parts = []
        for i, result in enumerate(search_results[:5]):
            filename = result['metadata']['filename']
            content = result['content']
            similarity = result['similarity']
            
            # Extract and enhance with Bible references
            bible_refs = self.bible_lookup.extract_bible_references(content)
            enhanced_content = content
            
            if bible_refs:
                scripture_additions = []
                for ref in bible_refs:
                    scripture_text = self.bible_lookup.get_scripture_text(ref)
                    if scripture_text and '[Scripture text for' not in scripture_text:
                        scripture_additions.append(f"\n\n{ref['reference']}: \"{scripture_text}\"")
                
                if scripture_additions:
                    enhanced_content += "\n\nReferenced Scriptures:" + "".join(scripture_additions)
            
            # Use filename as the document identifier instead of just numbers
            enhanced_context_parts.append(f"Document \"{filename}\" (relevance: {similarity:.3f}):\n{enhanced_content}\n")
        
        context = "\n".join(enhanced_context_parts)
        
        # Create prompt for Ollama
        prompt = f"""You are a document analysis assistant. Answer the user's question using the information provided in the context below. Be comprehensive and helpful while staying within the bounds of the provided content.

GUIDELINES:
- Base your answer primarily on the information provided in the context below
- When citing information, reference the actual document filenames (e.g., "As explained in 'My Father Scriptures.docx'...")
- Do NOT use phrases like "the documents suggest", "according to the documents", "the documents state"
- Answer directly and naturally using the provided information
- If the context provides relevant information but not a complete answer, work with what's available and indicate where information might be limited
- Only say you don't have enough information if the context is completely unrelated to the question

Context from sources:
{context}

User question: {query}

Provide a comprehensive answer based on the information provided above."""

        try:
            # Generate response using Ollama
            response = ollama.generate(
                model=self.ollama_config['model'],
                prompt=prompt,
                options={
                    'temperature': self.ollama_config['temperature'],
                    'num_predict': self.ollama_config['max_tokens']
                }
            )
            
            return response['response']
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from search results"""
        sources = []
        for result in search_results:
            metadata = result['metadata']
            sources.append({
                'filename': metadata['filename'],
                'filepath': metadata.get('filepath', ''),
                'similarity': result['similarity'],
                'document_id': metadata.get('document_id', '')
            })
        return sources
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query history"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_manager.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT query_text, results_count, execution_time, created_date
                FROM query_history 
                ORDER BY created_date DESC 
                LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'query': row[0],
                    'results_count': row[1],
                    'execution_time': row[2],
                    'created_date': row[3]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"Failed to get query history: {e}")
            return []
    
    def export_query_results(self, response_data: Dict[str, Any], output_file: str, format: str = 'text') -> bool:
        """Export query results to a file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format.lower() == 'text':
                    self._export_as_text(response_data, f)
                elif format.lower() == 'json':
                    import json
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    def _export_as_text(self, response_data: Dict[str, Any], file_handle):
        """Export results as formatted text"""
        file_handle.write(f"Query: {response_data['query']}\n")
        file_handle.write(f"Execution Time: {response_data['execution_time']:.3f} seconds\n")
        file_handle.write(f"Results Found: {len(response_data['search_results'])}\n")
        file_handle.write("=" * 80 + "\n\n")
        
        if response_data['llm_response']:
            file_handle.write("LLM RESPONSE:\n")
            file_handle.write("-" * 40 + "\n")
            file_handle.write(response_data['llm_response'])
            file_handle.write("\n\n")
        
        file_handle.write("SEARCH RESULTS:\n")
        file_handle.write("-" * 40 + "\n")
        
        for i, result in enumerate(response_data['search_results'], 1):
            file_handle.write(f"\n{i}. {result['metadata']['filename']} (Similarity: {result['similarity']:.3f})\n")
            file_handle.write(f"Content: {result['content']}\n")
        
        if response_data['sources_used']:
            file_handle.write("\n\nSOURCES:\n")
            file_handle.write("-" * 40 + "\n")
            for source in response_data['sources_used']:
                file_handle.write(f"- {source['filename']} (Similarity: {source['similarity']:.3f})\n")
    
    def search_by_scripture(self, scripture_query: str) -> List[Dict]:
        """Search for documents containing specific scripture references"""
        if not self.scripture_indexer:
            logger.warning("Scripture indexer not available")
            return []
        
        return self.scripture_indexer.search_by_scripture(scripture_query)
    
    def get_document_scriptures(self, document_id: int) -> List[Dict]:
        """Get all scripture references for a specific document"""
        if not self.scripture_indexer:
            logger.warning("Scripture indexer not available")
            return []
        
        return self.scripture_indexer.get_document_scriptures(document_id)
    
    def get_scripture_statistics(self) -> Dict:
        """Get statistics about scripture references in the database"""
        if not self.scripture_indexer:
            logger.warning("Scripture indexer not available")
            return {}
        
        return self.scripture_indexer.get_scripture_statistics()
    
    def query_with_scripture_filter(self, query_text: str, scripture_filter: str, use_llm: bool = True) -> Dict[str, Any]:
        """Query with scripture reference filtering"""
        start_time = time.time()
        
        # First, find documents containing the scripture reference
        scripture_results = self.search_by_scripture(scripture_filter)
        
        if not scripture_results:
            return {
                'query': query_text,
                'scripture_filter': scripture_filter,
                'search_results': [],
                'llm_response': f"No documents found containing scripture reference: {scripture_filter}",
                'execution_time': time.time() - start_time,
                'sources_used': []
            }
        
        # Get document IDs that contain the scripture
        doc_ids = [result['document_id'] for result in scripture_results]
        
        # Perform vector search only within these documents
        filtered_search_results = self.db_manager.search_similar_documents_filtered(
            query_text, 
            document_ids=doc_ids, 
            top_k=self.max_results
        )
        
        response_data = {
            'query': query_text,
            'scripture_filter': scripture_filter,
            'search_results': filtered_search_results,
            'scripture_matches': scripture_results,
            'llm_response': None,
            'execution_time': 0,
            'sources_used': []
        }
        
        if filtered_search_results and use_llm:
            try:
                # Generate contextual response using Ollama
                llm_response = self._generate_llm_response_with_scripture(
                    query_text, filtered_search_results, scripture_filter, scripture_results
                )
                response_data['llm_response'] = llm_response
                
                # Extract sources used
                if self.include_sources:
                    response_data['sources_used'] = self._extract_sources(filtered_search_results)
                    
            except Exception as e:
                logger.error(f"LLM response generation failed: {e}")
                response_data['llm_response'] = "Error generating LLM response. Vector search results available."
        
        execution_time = time.time() - start_time
        response_data['execution_time'] = execution_time
        
        return response_data
    
    def search_by_theological_concept(self, concept_query: str) -> List[Dict]:
        """Search for documents containing specific theological concepts"""
        if not self.theological_indexer:
            logger.warning("Theological indexer not available")
            return []
        
        # Convert single concept to list for the search method
        return self.theological_indexer.search_by_concepts([concept_query])

    def query_with_theological_and_scripture_filter(self, query_text: str, concept_filter: str, scripture_filter: str, use_llm: bool = True) -> Dict[str, Any]:
        """Query with both theological concept and scripture reference filtering"""
        start_time = time.time()
        
        # Find documents containing the theological concept
        concept_results = self.search_by_theological_concept(concept_filter)
        
        if not concept_results:
            return {
                'query': query_text,
                'concept_filter': concept_filter,
                'scripture_filter': scripture_filter,
                'search_results': [],
                'llm_response': f"No documents found containing theological concept: {concept_filter}",
                'execution_time': time.time() - start_time,
                'sources_used': []
            }

        # Find documents containing the scripture reference
        scripture_results = self.search_by_scripture(scripture_filter)

        if not scripture_results:
            return {
                'query': query_text,
                'concept_filter': concept_filter,
                'scripture_filter': scripture_filter,
                'search_results': [],
                'llm_response': f"No documents found containing scripture reference: {scripture_filter}",
                'execution_time': time.time() - start_time,
                'sources_used': []
            }
        
        # Find document IDs that contain both filters
        concept_doc_ids = set(result['document_id'] for result in concept_results)
        scripture_doc_ids = set(result['document_id'] for result in scripture_results)
        combined_doc_ids = list(concept_doc_ids.intersection(scripture_doc_ids))
        
        if not combined_doc_ids:
            return {
                'query': query_text,
                'concept_filter': concept_filter,
                'scripture_filter': scripture_filter,
                'search_results': [],
                'llm_response': "No documents found meeting both filter criteria.",
                'execution_time': time.time() - start_time,
                'sources_used': []
            }

        # Perform vector search within filtered documents
        filtered_search_results = self.db_manager.search_similar_documents_filtered(
            query_text, 
            document_ids=combined_doc_ids, 
            top_k=self.max_results
        )

        response_data = {
            'query': query_text,
            'concept_filter': concept_filter,
            'scripture_filter': scripture_filter,
            'search_results': filtered_search_results,
            'theological_matches': concept_results,
            'scripture_matches': scripture_results,
            'llm_response': None,
            'execution_time': 0,
            'sources_used': []
        }

        if filtered_search_results and use_llm:
            try:
                llm_response = self._generate_llm_response_with_theology_and_scripture(
                    query_text, filtered_search_results, concept_filter, concept_results, scripture_filter, scripture_results
                )
                response_data['llm_response'] = llm_response

                if self.include_sources:
                    response_data['sources_used'] = self._extract_sources(filtered_search_results)
                
            except Exception as e:
                logger.error(f"LLM response generation failed: {e}")
                response_data['llm_response'] = "Error generating LLM response. Vector search results available."

        execution_time = time.time() - start_time
        response_data['execution_time'] = execution_time

        return response_data

    def _generate_llm_response_with_theology_and_scripture(self, query: str, search_results: List[Dict], 
                                                            concept_filter: str, concept_matches: List[Dict],
                                                            scripture_filter: str, scripture_matches: List[Dict]) -> str:
        """Generate LLM response using both theological and scripture context"""

        # Prepare context from search results as previously done
        context_parts = []
        for i, result in enumerate(search_results[:5]):
            filename = result['metadata']['filename']
            content = result['content']
            similarity = result['similarity']

            # Use filename as the document identifier instead of just numbers
            context_parts.append(f"Document \"{filename}\" (relevance: {similarity:.3f}):\n{content}\n")

        # Add theological context
        theological_context = [f"Theological concept '{concept_filter}' found in documents:"]
        for match in concept_matches[:3]:
            theological_context.append(f"- {match['filename']} - Context: {','.join(match['contexts'][:2])}")

        # Add scripture context
        scripture_context = [f"Scripture references for '{scripture_filter}' found in documents:"]
        for match in scripture_matches[:3]:
            scripture_context.append(f"- {match['filename']} - Context: {','.join(match['context_snippets'][:2])}")

        context = "\n".join(context_parts)
        theological_info = "\n".join(theological_context)
        scripture_info = "\n".join(scripture_context)

        # Create enhanced prompt
        prompt = f"""Based on the documents containing the theological concept "{concept_filter}" and the scripture reference "{scripture_filter}", please answer the user's question.
\nTheological Context:
{theological_info}
\nScripture Reference Context:
{scripture_info}
\nDocument Content:
{context}
\nUser question: {query}
\nProvide a detailed answer how the theological concept and the scripture are related to the user's query."""

        try:
            response = ollama.generate(
                model=self.ollama_config['model'],
                prompt=prompt,
                options={
                    'temperature': self.ollama_config['temperature'],
                    'num_predict': self.ollama_config['max_tokens']
                }
            )
            return response['response']

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _generate_llm_response_with_scripture(self, query: str, search_results: List[Dict], 
                                            scripture_filter: str, scripture_matches: List[Dict]) -> str:
        """Generate LLM response enhanced with scripture context"""
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5]):
            filename = result['metadata']['filename']
            content = result['content']
            similarity = result['similarity']
            
            # Use filename as the document identifier instead of just numbers
            context_parts.append(f"Document \"{filename}\" (relevance: {similarity:.3f}):\n{content}\n")
        
        # Add scripture context
        scripture_context = []
        for match in scripture_matches[:3]:  # Show top 3 scripture matches
            scripture_context.append(f"Scripture {match['normalized_reference']} found in {match['filename']}")
            if match['context_snippets']:
                scripture_context.append(f"Context: {match['context_snippets'][0][:200]}...")
        
        context = "\n".join(context_parts)
        scripture_info = "\n".join(scripture_context)
        
        # Create enhanced prompt
        prompt = f"""Based on the following documents that contain the scripture reference "{scripture_filter}", please answer the user's question.

Scripture Reference Context:
{scripture_info}

Document Content:
{context}

User question: {query}

Please provide a comprehensive answer that specifically addresses how the scripture reference "{scripture_filter}" relates to the question, based on the information in the documents."""
        
        try:
            response = ollama.generate(
                model=self.ollama_config['model'],
                prompt=prompt,
                options={
                    'temperature': self.ollama_config['temperature'],
                    'num_predict': self.ollama_config['max_tokens']
                }
            )
            
            return response['response']
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
