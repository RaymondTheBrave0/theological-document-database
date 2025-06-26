#!/usr/bin/env python3
# Document Database Main Application

import os
import sys
import yaml
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.initialize_database import initialize_database
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel
from src.document_processor import DocumentProcessor

# Load configuration
def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Setup logging
def setup_logging(config):
    logging.basicConfig(
        level=config['logging']['level'],
        format='%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[RichHandler()]
    )
    logger = logging.getLogger()
    logger.setLevel(config['logging']['level'])
    return logger

# Main entry point
def main():
    console = Console()
    
    try:
        # Load configuration
        config_path = Path(__file__).parent.parent / 'config.yaml'
        config = load_config(config_path)
        logger = setup_logging(config)
        
        console.print(Panel("Document Database System", style="bold blue"))
        logger.info("Starting Document Database...")

        # Initialize database
        db_manager = initialize_database(config)

        # Process documents
        document_processor = DocumentProcessor(config, db_manager)
        input_directory = config['document_processing']['input_folder']
        logger.info(f"Processing documents in {input_directory} ...")
        document_processor.process_directory(input_directory)

        # Display updated database stats
        stats = db_manager.get_database_stats()
        console.print(f"\n[green]Database processed successfully![/green]")
        console.print(f"Documents: {stats['document_count']}")
        console.print(f"Chunks: {stats['chunk_count']}")
        console.print(f"Vectors: {stats['vector_count']}")
        console.print(f"Total file size: {stats['total_file_size']} bytes")

        logger.info("Document Database is operational.")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
