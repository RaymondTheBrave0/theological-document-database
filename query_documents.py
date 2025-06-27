#!/usr/bin/env python3
"""
Document Database Terminal Query Interface
Multi-database support for terminal-based queries
"""

import os
import sys
import argparse
import click
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database_config import add_database_args, handle_database_selection, get_database_config, DatabaseConfig
from src.terminal_interface import TerminalInterface


class MultiDatabaseTerminalInterface(TerminalInterface):
    """Extended terminal interface with multi-database support"""
    
    def __init__(self, db_id=None, auto_save=True, use_ai=True):
        self.db_id = db_id
        self.database_name = None
        super().__init__(auto_save=auto_save, use_ai=use_ai)
    
    def _load_config(self):
        """Load database-specific configuration"""
        try:
            # Get database-specific configuration
            self.config, resolved_db_id = get_database_config(self.db_id)
            self.db_id = resolved_db_id
            
            # Get database name for display
            db_config = DatabaseConfig()
            db_info = db_config.get_database_info(self.db_id)
            self.database_name = db_info['name'] if db_info else f"Database {self.db_id}"
            
            # Print database information
            db_config.print_database_summary(self.db_id)
            
        except Exception as e:
            self.console.print(f"[red]Database configuration error: {e}[/red]")
            self.console.print("[yellow]💡 Use 'manage_databases.py list' to see available databases[/yellow]")
            sys.exit(1)
    
    def show_banner(self):
        """Display application banner with database information"""
        from rich.text import Text
        from rich.panel import Panel
        
        banner_text = Text(f"Document Database Query System", style="bold blue")
        stats = self.db_manager.get_database_stats()
        
        info_text = f"""
🗄️  Database: {self.database_name} ({self.db_id})
📚 Documents: {stats['document_count']}
📄 Chunks: {stats['chunk_count']}
🔍 Vectors: {stats['vector_count']}
💾 Total Size: {stats['total_file_size']} bytes

Commands:
• Type your query to search documents
• 'history' - View recent queries  
• 'stats' - Show database statistics
• 'help' - Show this help
• 'exit' or 'quit' - Exit application
        """
        
        panel = Panel(info_text, title=f"[bold blue]{self.database_name}[/bold blue]", border_style="blue")
        self.console.print(panel)
    
    def show_help(self):
        """Display help information with database context"""
        help_text = f"""
[bold cyan]Document Database Terminal Interface[/bold cyan]
[dim]Current Database: {self.database_name} ({self.db_id})[/dim]

[bold]Query Commands:[/bold]
• Simply type your search terms to query the database
• Use natural language questions for best AI responses
• scripture:reference - Search for specific scripture references
• concept:term - Search for theological concepts

[bold]System Commands:[/bold]
• help           - Show this help message
• history        - View recent query history
• stats          - Show database statistics
• scripture-stats - Show scripture reference statistics
• concept-stats  - Show theological concept statistics
• clear          - Clear the screen
• exit           - Exit the application

[bold]Advanced Queries:[/bold]
• 'query scripture:reference' - Filter results by scripture
• Use specific terms for better search results

[bold]Tips:[/bold]
• Enable AI responses for detailed explanations
• Results are automatically saved to history
• Press Ctrl+C to cancel current operation
• Use --db-id to switch between theological databases
        """
        
        from rich.panel import Panel
        panel = Panel(help_text, title="[bold cyan]Help[/bold cyan]", border_style="cyan")
        self.console.print(panel)


@click.command()
@click.option('--query', '-q', help='Execute a single query and exit')
@click.option('--output', '-o', help='Output file for results')
@click.option('--no-ai', is_flag=True, help='Disable AI response generation')
@click.option('--no-save', is_flag=True, help='Disable automatic saving of results to file')
@click.option('--db-id', '--database-id', help='Database ID to use (4-digit number)')
@click.option('--list-databases', is_flag=True, help='List all available databases and exit')
def main(query, output, no_ai, no_save, db_id, list_databases):
    """
    Document Database Terminal Query Interface
    
    Interactive terminal for querying your theological document databases with AI assistance.
    
    Examples:
      query_documents.py                    # Use default database
      query_documents.py --db-id 1003      # Use Eschatology database
      query_documents.py --list-databases  # Show available databases
      query_documents.py -q "salvation"    # Single query mode
    """
    
    # Handle database listing
    if list_databases:
        try:
            db_config = DatabaseConfig()
            print("📂 Available Databases:")
            print("=" * 50)
            for database_id in db_config.list_database_ids():
                db_info = db_config.get_database_info(database_id)
                default_marker = " [DEFAULT]" if database_id == db_config.get_default_database_id() else ""
                print(f"🔹 {database_id}{default_marker}: {db_info['name']}")
                print(f"   {db_info['description'][:100]}{'...' if len(db_info['description']) > 100 else ''}")
            return 0
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            return 1
    
    try:
        # Initialize interface with database support
        auto_save = not no_save
        use_ai = not no_ai
        interface = MultiDatabaseTerminalInterface(
            db_id=db_id, 
            auto_save=auto_save, 
            use_ai=use_ai
        )
        
        if query:
            # Single query mode
            use_llm = not no_ai
            response = interface.query_engine.query(query, use_llm=use_llm)
            interface.display_response(response)
            
            if output:
                success = interface.query_engine.export_query_results(response, output, 'text')
                if success:
                    interface.console.print(f"[green]Results saved to:[/green] {output}")
        else:
            # Interactive mode
            interface.run()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Use --list-databases to see available databases")
        return 1


if __name__ == '__main__':
    sys.exit(main())
