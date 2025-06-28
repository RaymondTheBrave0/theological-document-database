#!/usr/bin/env python3
"""
Enhanced Terminal Interface for Document Database System
"""

import os
import sys
import yaml
import logging
import click
from pathlib import Path
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import track

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.initialize_database import initialize_database
from src.query_engine import QueryEngine
from src.database_config import add_database_args, handle_database_selection, get_database_config, DatabaseConfig

class TerminalInterface:
    """Interactive terminal interface for document database queries"""
    
    def __init__(self, auto_save=True, use_ai=True):
        self.console = Console()
        self.config = None
        self.db_manager = None
        self.query_engine = None
        self.session = None
        self.auto_save = auto_save
        self.use_ai = use_ai
        
        # Load configuration and initialize
        self._load_config()
        self._initialize_components()
        self._setup_prompt_session()
    
    def _load_config(self):
        """Load configuration from config.yaml"""
        try:
            config_path = Path(__file__).parent.parent / 'config.yaml'
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.console.print(f"[red]Error loading configuration: {e}[/red]")
            sys.exit(1)
    
    def _initialize_components(self):
        """Initialize database manager and query engine"""
        try:
            self.db_manager = initialize_database(self.config)
            self.query_engine = QueryEngine(self.config, self.db_manager)
        except Exception as e:
            self.console.print(f"[red]Error initializing components: {e}[/red]")
            sys.exit(1)
    
    def _setup_prompt_session(self):
        """Setup prompt session with history and styling"""
        history_file = self.config['terminal']['history_file']
        
        style = Style.from_dict({
            'prompt': '#ansigreen bold',
            'path': '#ansicyan',
            'pound': '#ansiwhite bold',
            'bracket': '#ansiwhite bold',
        })
        
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            style=style
        )
    
    def show_banner(self):
        """Display application banner"""
        banner_text = Text("Document Database Query System", style="bold blue")
        stats = self.db_manager.get_database_stats()
        
        info_text = f"""
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
        
        panel = Panel(info_text, title="[bold blue]Document Database[/bold blue]", border_style="blue")
        self.console.print(panel)
    
    def run(self):
        """Main interactive loop"""
        self.show_banner()
        
        while True:
            try:
                # Get user input
                query = self.session.prompt(
                    HTML('<prompt>Query</prompt> <bracket>[</bracket><path>DocDB</path><bracket>]</bracket><pound>></pound> ')
                ).strip()
                
                if not query:
                    continue
                
                # Handle special commands
                if query.lower() in ['exit', 'quit', 'q']:
                    break
                elif query.lower() == 'help':
                    self.show_help()
                elif query.lower() == 'history':
                    self.show_history()
                elif query.lower() == 'stats':
                    self.show_stats()
                elif query.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                elif query.lower().startswith('scripture:'):
                    # Scripture search command
                    scripture_ref = query[10:].strip()
                    self.process_scripture_query(scripture_ref)
                elif query.lower() == 'scripture-stats':
                    self.show_scripture_stats()
                elif query.lower().startswith('concept:'):
                    # Theological concept search command
                    concept = query[8:].strip()
                    self.process_concept_query(concept)
                elif query.lower() == 'concept-stats':
                    self.show_concept_stats()
                else:
                    # Check if it's a scripture filter query
                    if ' scripture:' in query.lower():
                        self.process_combined_query(query)
                    else:
                        # Process regular query
                        self.process_query(query)
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
        
        self.console.print("\n[yellow]Goodbye![/yellow]")
    
    def process_query(self, query: str):
        """Process a user query"""
        self.console.print(f"\n🔍 [bold]Searching for:[/bold] '{query}'")
        
        # Use AI if enabled and available
        use_llm = self.use_ai
        try:
            if not self.query_engine.ollama_config:
                use_llm = False
        except:
            use_llm = False
        
        # Ask if user wants sources shown
        show_sources = False
        try:
            show_sources = confirm("Show document sources? (y/n)")
        except:
            show_sources = False
        
        # Execute query
        with self.console.status("[bold green]Processing query...") as status:
            response = self.query_engine.query(query, use_llm=use_llm)
        
        # Display results
        self.display_response(response, show_sources=show_sources)
        
        # Auto-save results if enabled
        if response['search_results'] and self.auto_save:
            self.save_results(response)
    
    def display_response(self, response: dict, show_sources: bool = False):
        """Display query response in formatted output"""
        
        # Show LLM response if available
        if response['llm_response']:
            llm_panel = Panel(
                response['llm_response'], 
                title="[bold green]AI Response[/bold green]",
                border_style="green"
            )
            self.console.print(llm_panel)
        
    
    def _extract_full_content(self, content: str, query: str) -> str:
        """Extract full sentences or paragraphs containing the query context"""
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
    
    def save_results(self, response: dict):
        """Save query results to daily file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"queries_{date_str}.txt"
        output_path = Path(self.config['output']['default_output_folder']) / filename
        
        try:
            success = self._append_to_daily_file(response, str(output_path))
            if success:
                self.console.print(f"[green]Results saved to:[/green] {filename}")
            else:
                self.console.print("[red]Failed to save results[/red]")
        except Exception as e:
            self.console.print(f"[red]Error saving results: {e}[/red]")
    
    def _append_to_daily_file(self, response_data: dict, file_path: str) -> bool:
        """Append query results to daily file"""
        try:
            # Ensure output directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists to determine if we need a header
            file_exists = Path(file_path).exists()
            
            with open(file_path, 'a', encoding='utf-8') as f:
                # Add date header for new files
                if not file_exists:
                    f.write(f"Document Database Query Log - {datetime.now().strftime('%Y-%m-%d')}\n")
                    f.write("=" * 80 + "\n\n")
                
                # Add timestamp and query
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f"[{timestamp}] Query: {response_data['query']}\n")
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
            logging.error(f"Failed to append to daily file: {e}")
            return False
    
    def show_help(self):
        """Display help information"""
        help_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold]Query Commands:[/bold]
• Simply type your search terms to query the database
• Use natural language questions for best AI responses

[bold]System Commands:[/bold]
• help     - Show this help message
• history  - View recent query history
• stats    - Show database statistics  
• clear    - Clear the screen
• exit     - Exit the application

[bold]Tips:[/bold]
• Use specific terms for better search results
• Enable AI responses for detailed explanations
• Results are automatically saved to history
• Press Ctrl+C to cancel current operation
        """
        
        panel = Panel(help_text, title="[bold cyan]Help[/bold cyan]", border_style="cyan")
        self.console.print(panel)
    
    def show_history(self):
        """Display recent query history"""
        history = self.query_engine.get_query_history(limit=10)
        
        if not history:
            self.console.print("[yellow]No query history found[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta", title="Recent Queries")
        table.add_column("Date", width=20)
        table.add_column("Query", min_width=30)
        table.add_column("Results", justify="right", width=8)
        table.add_column("Time", justify="right", width=8)
        
        for entry in history:
            date = entry['created_date'][:19]  # Remove microseconds
            query = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']
            results = str(entry['results_count'])
            exec_time = f"{entry['execution_time']:.3f}s"
            
            table.add_row(date, query, results, exec_time)
        
        self.console.print(table)
    
    def show_stats(self):
        """Display database statistics"""
        stats = self.db_manager.get_database_stats()
        
        stats_text = f"""
[bold cyan]Database Statistics:[/bold cyan]

📚 Total Documents: {stats['document_count']}
📄 Total Chunks: {stats['chunk_count']}
🔍 Vector Entries: {stats['vector_count']}
💾 Total File Size: {stats['total_file_size']:,} bytes

[bold cyan]File Type Distribution:[/bold cyan]
        """
        
        for file_type, count in stats.get('file_type_distribution', {}).items():
            stats_text += f"\n• {file_type}: {count} files"
        
        panel = Panel(stats_text, title="[bold cyan]Statistics[/bold cyan]", border_style="cyan")
        self.console.print(panel)
    
    def process_scripture_query(self, scripture_ref: str):
        """Process a scripture reference search"""
        self.console.print(f"\n📖 [bold]Searching for scripture:[/bold] '{scripture_ref}'")
        
        with self.console.status("[bold green]Searching scripture references...") as status:
            results = self.query_engine.search_by_scripture(scripture_ref)
        
        if results:
            table = Table(show_header=True, header_style="bold magenta", title=f"Documents containing '{scripture_ref}'")
            table.add_column("Document", min_width=30)
            table.add_column("Reference", width=20)
            table.add_column("Normalized", width=20)
            table.add_column("Context")
            
            for result in results:
                context = "; ".join(result['context_snippets'][:2]) if result['context_snippets'] else "No context"
                if len(context) > 100:
                    context = context[:100] + "..."
                
                table.add_row(
                    result['filename'],
                    result['reference'],
                    result['normalized_reference'],
                    context
                )
            
            self.console.print(table)
            self.console.print(f"\n[dim]Found {len(results)} document(s) containing the scripture reference[/dim]")
        else:
            self.console.print(f"[yellow]No documents found containing scripture reference: {scripture_ref}[/yellow]")
    
    def show_scripture_stats(self):
        """Display scripture indexing statistics"""
        stats = self.query_engine.get_scripture_statistics()
        
        if not stats:
            self.console.print("[yellow]Scripture indexing not available or no data found[/yellow]")
            return
        
        stats_text = f"""
[bold cyan]Scripture Reference Statistics:[/bold cyan]

📖 Total Scripture References: {stats.get('total_references', 0):,}
📚 Unique Scripture References: {stats.get('unique_references', 0):,}

[bold cyan]Top Scripture References:[/bold cyan]
"""
        
        if stats.get('top_scriptures'):
            for i, ref_data in enumerate(stats['top_scriptures'][:10], 1):
                stats_text += f"\n{i:2d}. {ref_data['reference']} - {ref_data['document_count']} documents"
        
        panel = Panel(stats_text, title="[bold cyan]Scripture Statistics[/bold cyan]", border_style="cyan")
        self.console.print(panel)
    
    def process_combined_query(self, query: str):
        """Process a query with scripture filtering"""
        # Parse the query to extract main query and scripture filter
        parts = query.lower().split(' scripture:')
        if len(parts) != 2:
            self.console.print("[red]Invalid format. Use: 'your query scripture: reference'[/red]")
            return
        
        main_query = parts[0].strip()
        scripture_filter = parts[1].strip()
        
        self.console.print(f"\n🔍 [bold]Query:[/bold] '{main_query}'")
        self.console.print(f"📖 [bold]Scripture Filter:[/bold] '{scripture_filter}'")
        
        # Use AI if enabled and available
        use_llm = self.use_ai
        try:
            if not self.query_engine.ollama_config:
                use_llm = False
        except:
            use_llm = False
        
        # Execute query with scripture filter
        with self.console.status("[bold green]Processing filtered query...") as status:
            response = self.query_engine.query_with_scripture_filter(
                main_query, scripture_filter, use_llm=use_llm
            )
        
        # Display results
        self.display_scripture_filtered_response(response)
        
        # Auto-save results if enabled
        if response['search_results'] and self.auto_save:
            self.save_results(response)
    
    def display_scripture_filtered_response(self, response: dict):
        """Display scripture-filtered query response"""
        
        # Show scripture matches first
        if response.get('scripture_matches'):
            self.console.print(f"\n[bold green]Scripture Matches[/bold green] ({len(response['scripture_matches'])} found)")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Document", min_width=25)
            table.add_column("Reference", width=20)
            table.add_column("Context")
            
            for match in response['scripture_matches'][:5]:  # Show top 5
                context = "; ".join(match['context_snippets'][:1]) if match['context_snippets'] else "No context"
                if len(context) > 80:
                    context = context[:80] + "..."
                
                table.add_row(
                    match['filename'],
                    match['normalized_reference'],
                    context
                )
            
            self.console.print(table)
        
        # Show LLM response if available
        if response['llm_response']:
            llm_panel = Panel(
                response['llm_response'], 
                title="[bold green]AI Response (Scripture-Filtered)[/bold green]",
                border_style="green"
            )
            self.console.print(llm_panel)
        
    
    def process_concept_query(self, concept: str):
        """Process a theological concept search"""
        self.console.print(f"\n🔍 [bold]Searching for theological concept:[/bold] '{concept}'")
        
        with self.console.status("[bold green]Searching theological concepts...") as status:
            results = self.query_engine.search_by_theological_concept(concept)
        
        if results:
            table = Table(show_header=True, header_style="bold magenta", title=f"Documents containing '{concept}'")
            table.add_column("Document", min_width=30)
            table.add_column("Concept", width=20)
            table.add_column("Context")
            
            for result in results:
                context = "; ".join(result['contexts'][:2]) if result['contexts'] else "No context"
                if len(context) > 100:
                    context = context[:100] + "..."
                
                table.add_row(
                    result['filename'],
                    result['concept'],
                    context
                )
            
            self.console.print(table)
            self.console.print(f"\n[dim]Found {len(results)} document(s) containing the theological concept[/dim]")
        else:
            self.console.print(f"[yellow]No documents found containing theological concept: {concept}[/yellow]")
    
    def show_concept_stats(self):
        """Display theological concept statistics"""
        if not self.query_engine.theological_indexer:
            self.console.print("[yellow]Theological indexer not available[/yellow]")
            return
        
        stats = self.query_engine.theological_indexer.get_concept_statistics()
        
        if not stats:
            self.console.print("[yellow]Theological concept indexing not available or no data found[/yellow]")
            return
        
        stats_text = f"""
[bold cyan]Theological Concept Statistics:[/bold cyan]

🔍 Total Concept References: {stats.get('total_concepts', 0):,}
📚 Unique Concepts: {stats.get('unique_concepts', 0):,}

[bold cyan]Top Theological Concepts:[/bold cyan]
"""
        
        if stats.get('top_concepts'):
            for i, concept_data in enumerate(stats['top_concepts'][:10], 1):
                stats_text += f"\n{i:2d}. {concept_data['concept']} - {concept_data['document_count']} documents"
        
        panel = Panel(stats_text, title="[bold cyan]Theological Concept Statistics[/bold cyan]", border_style="cyan")
        self.console.print(panel)


@click.command()
@click.option('--query', '-q', help='Execute a single query and exit')
@click.option('--output', '-o', help='Output file for results')
@click.option('--no-ai', is_flag=True, help='Disable AI response generation')
@click.option('--no-save', is_flag=True, help='Disable automatic saving of results to file')
def main(query, output, no_ai, no_save):
    """
    Document Database Terminal Interface
    
    Interactive terminal for querying your document database with AI assistance.
    """
    auto_save = not no_save  # Default is True unless --no-save is specified
    use_ai = not no_ai      # Default is True unless --no-ai is specified
    interface = TerminalInterface(auto_save=auto_save, use_ai=use_ai)
    
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


if __name__ == '__main__':
    main()
