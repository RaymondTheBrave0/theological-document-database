#!/usr/bin/env python3
"""
Web GUI for Document Database System
Flask application with modern interface
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.initialize_database import initialize_database
from src.query_engine import QueryEngine
from src.document_processor import DocumentProcessor
from src.database_config import get_database_config, DatabaseConfig

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../web/templates',
           static_folder='../web/static')
app.config['SECRET_KEY'] = 'doc_db_secret_key_2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
db_manager = None
query_engine = None
document_processor = None
config = None

# Default settings (can be overridden via API)
USE_AI_DEFAULT = True
AUTO_SAVE_DEFAULT = True

def initialize_app(db_id=None):
    """Initialize the application components with multi-database support"""
    global db_manager, query_engine, document_processor, config
    
    try:
        # Get database-specific configuration
        config, resolved_db_id = get_database_config(db_id)
        
        # Print database information
        db_config = DatabaseConfig()
        db_config.print_database_summary(resolved_db_id)
        
        # Initialize components
        db_manager = initialize_database(config)
        query_engine = QueryEngine(config, db_manager)
        document_processor = DocumentProcessor(config, db_manager)
        
        print("✓ Web application initialized successfully")
        return resolved_db_id
                
    except Exception as e:
        print(f"❌ Failed to initialize web application: {e}")
        print("💡 Use 'manage_databases.py list' to see available databases")
        sys.exit(1)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query_documents():
    """Process document query"""
    try:
        data = request.get_json()
        query_text = data.get('query', '').strip()
        use_llm = data.get('use_llm', USE_AI_DEFAULT)  # Default to True
        auto_save = data.get('auto_save', AUTO_SAVE_DEFAULT)  # Default to True
        top_k = data.get('top_k', 10)  # Increased default results
        
        if not query_text:
            return jsonify({
                'success': False,
                'error': 'Query text is required'
            }), 400
        
        # Process query
        response = query_engine.query(query_text, use_llm=use_llm, top_k=top_k)
        
        # Note: Search results are not sent to frontend (AI response only)
        
        # Auto-save results if enabled
        saved_filename = None
        if auto_save and response['search_results']:
            try:
                saved_filename = _auto_save_results(response)
            except Exception as e:
                print(f"Auto-save failed: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'query': response['query'],
                'llm_response': response['llm_response'],
                'execution_time': response['execution_time'],
                'saved_filename': saved_filename,
                'auto_save_enabled': auto_save
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/database-info')
def get_database_info():
    """Get current database information"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'database_id': config['database']['database_id'],
                'database_name': config['database']['database_name'],
                'database_description': config['database']['database_description'],
                'document_folder': config['document_processing']['input_folder'],
                'stats': db_manager.get_database_stats() if db_manager else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history')
def get_query_history():
    """Get query history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = query_engine.get_query_history(limit=limit)
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_documents():
    """Upload and process documents"""
    try:
        # This is a placeholder - in a real implementation,
        # you'd handle file uploads here
        return jsonify({
            'success': True,
            'message': 'Document upload functionality coming soon'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export', methods=['POST'])
def export_results():
    """Export query results"""
    try:
        data = request.get_json()
        query_data = data.get('query_data')
        format_type = data.get('format', 'text')
        
        if not query_data:
            return jsonify({
                'success': False,
                'error': 'Query data is required'
            }), 400
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_export_{timestamp}.{format_type}"
        output_path = Path(config['output']['default_output_folder']) / filename
        
        # Export results
        success = query_engine.export_query_results(query_data, str(output_path), format_type)
        
        if success:
            return jsonify({
                'success': True,
                'filename': filename,
                'path': str(output_path)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to export results'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# SocketIO events for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'message': 'Connected to Document Database'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('query_stream')
def handle_query_stream(data):
    """Handle streaming query for real-time updates"""
    try:
        query_text = data.get('query', '').strip()
        use_llm = data.get('use_llm', True)
        
        if not query_text:
            emit('query_error', {'error': 'Query text is required'})
            return
        
        # Emit status update
        emit('query_status', {'status': 'Processing query...', 'step': 1, 'total': 3})
        
        # Perform vector search
        search_results = db_manager.search_similar_documents(query_text, top_k=5)
        emit('query_status', {'status': 'Vector search complete', 'step': 2, 'total': 3})
        emit('search_results', {'results': search_results})
        
        if search_results and use_llm:
            emit('query_status', {'status': 'Generating AI response...', 'step': 3, 'total': 3})
            
            # Generate LLM response
            try:
                llm_response = query_engine._generate_llm_response(query_text, search_results)
                emit('llm_response', {'response': llm_response})
                emit('query_status', {'status': 'Complete', 'step': 3, 'total': 3})
            except Exception as e:
                emit('query_error', {'error': f'LLM generation failed: {str(e)}'})
        else:
            emit('query_status', {'status': 'Complete', 'step': 3, 'total': 3})
            
    except Exception as e:
        emit('query_error', {'error': str(e)})

def _extract_full_content(content: str, query: str) -> str:
    """Extract full sentences or paragraphs containing the query context (same as terminal)"""
    import re
    
    # First try to split by paragraphs (double newlines)
    paragraphs = re.split(r'\n\s*\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # Find paragraphs containing query terms
    query_words = [word.lower() for word in query.split() if len(word) > 2]  # Skip short words
    relevant_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        # Count how many query words are in this paragraph
        word_matches = sum(1 for word in query_words if word in paragraph_lower)
        if word_matches > 0:
            relevant_paragraphs.append((paragraph, word_matches))
    
    if relevant_paragraphs:
        # Sort by number of matching words and take the best
        relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
        best_paragraph = relevant_paragraphs[0][0]
        
        # If paragraph is reasonable length, return it as is
        if len(best_paragraph) <= 500:
            return best_paragraph
        else:
            # If too long, try to extract relevant sentences from the paragraph
            sentences = re.split(r'[.!?]+', best_paragraph)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            relevant_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                word_matches = sum(1 for word in query_words if word in sentence_lower)
                if word_matches > 0:
                    relevant_sentences.append((sentence, word_matches))
            
            if relevant_sentences:
                # Take the top 2-3 most relevant sentences
                relevant_sentences.sort(key=lambda x: x[1], reverse=True)
                top_sentences = [s[0] for s in relevant_sentences[:3]]
                return '. '.join(top_sentences) + '.'
            else:
                # Fallback to first part of paragraph
                return best_paragraph[:400] + "..."
    
    # If no paragraphs match, try sentences from the whole content
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        word_matches = sum(1 for word in query_words if word in sentence_lower)
        if word_matches > 0:
            relevant_sentences.append((sentence, word_matches))
    
    if relevant_sentences:
        # Sort by relevance and take top sentences
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in relevant_sentences[:2]]
        return '. '.join(top_sentences) + '.'
    
    # Fallback to beginning of content
    if len(content) <= 300:
        return content
    else:
        return content[:300] + "..."

def _auto_save_results(response_data: dict) -> str:
    """Auto-save query results to daily file and return filename"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"web_queries_{date_str}.txt"
    output_path = Path(config['output']['default_output_folder']) / filename
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    success = _append_to_daily_file(response_data, str(output_path))
    if success:
        return filename
    else:
        raise Exception("Failed to save results")

def _append_to_daily_file(response_data: dict, file_path: str) -> bool:
    """Append query results to daily file"""
    try:
        # Check if file exists to determine if we need a header
        file_exists = Path(file_path).exists()
        
        with open(file_path, 'a', encoding='utf-8') as f:
            # Add date header for new files
            if not file_exists:
                f.write(f"Document Database Web Query Log - {datetime.now().strftime('%Y-%m-%d')}\n")
                f.write("=" * 80 + "\n\n")
            
            # Add timestamp and query
            timestamp = datetime.now().strftime('%H:%M:%S')
            f.write(f"[{timestamp}] Web Query: {response_data['query']}\n")
            f.write(f"Execution Time: {response_data['execution_time']:.3f} seconds\n")
            f.write("-" * 60 + "\n")
            
            # Add AI response if available
            if response_data.get('llm_response'):
                f.write("AI Response:\n")
                f.write(response_data['llm_response'])
                f.write("\n")
            else:
                f.write("No AI response generated.\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
        
        return True
        
    except Exception as e:
        print(f"Failed to append to daily file: {e}")
        return False

def main():
    """Main entry point"""
    initialize_app()
    
    # Suppress all Flask startup messages and debug output
    import logging
    import sys
    import os
    
    # Set all logging to critical level
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Suppress all Flask-related loggers
    for logger_name in ['werkzeug', 'flask', 'flask.app', 'socketio', 'engineio']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.disabled = True
        logger.propagate = False
    
    # Get host and port from config
    host = config['web']['host']
    port = config['web']['port']
    debug = config['web']['debug']
    
    # Redirect all output to suppress any remaining messages
    with open(os.devnull, 'w') as devnull:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        
        try:
            # Run the application with all output suppressed
            socketio.run(app, host=host, port=port, debug=False, log_output=False, use_reloader=False)
        finally:
            # Restore output streams
            sys.stdout = original_stdout
            sys.stderr = original_stderr

if __name__ == '__main__':
    main()
