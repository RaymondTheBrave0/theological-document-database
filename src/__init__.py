"""
Document Database System

A comprehensive document management system using Python and Ollama.
Supports multiple document formats and provides both terminal and web-based query interfaces.
"""

from .initialize_database import initialize_database
from .database_manager import DatabaseManager
from .document_processor import DocumentProcessor

__version__ = "1.0.0"
__author__ = "Document Database System"

# Package-level imports
__all__ = [
    'initialize_database',
    'DatabaseManager',
    'DocumentProcessor',
]
