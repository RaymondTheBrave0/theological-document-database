#!/usr/bin/env python3
"""
Terminal query interface for Document Database System
"""

import os
import click
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from src import initialize_database, DocumentProcessor, DatabaseManager

# Command-line interface
@click.command()
@click.argument('query', required=True, nargs=-1)
@click.option('--output-file', '-o', type=click.Path(), help='File to write query results to')
@click.option('--top-k', default=5, help='Number of top results to return')
def query_interface(query, output_file, top_k):
    """
    Query the document database. Enter QUERY terms to search.
    """
    console = Console()
    
    # Load configuration
    config_path = 'config.yaml'
    config = initialize_database.load_config(config_path)
    
    # Initialize database manager
    db_manager = initialize_database.initialize_database(config)
    
    # Start query session if no query is provided
    if not query:
        session = PromptSession(message='Query: ', style=get_prompt_style())
        with patch_stdout():  # Allow prompt-toolkit to work with applications using stdout
            while True:
                try:
                    query = session.prompt().strip()
                    if query.lower() in ('exit', 'quit'):
                        break
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
                process_query(query, db_manager, console, output_file, top_k)
    else:
        query_str = ' '.join(query)
        process_query(query_str, db_manager, console, output_file, top_k)


def get_prompt_style():
    """Set prompt style for the terminal interface."""
    return Style.from_dict({
        '': '#d4d4d4',
        'prompt': 'bold #008f81'
    })


def process_query(query, db_manager, console, output_file, top_k):
    """Process the user query by searching the database and displaying results."""
    console.print(f"\n🔍 [bold]Searching for:[/bold] '{query}'")
    
    # Perform search
    results = db_manager.search_similar_documents(query, top_k=top_k)
    if not results:
        console.print("[red]No results found[/red]")
        return
    
    # Display results
    table = Table(show_header=True, header_style='bold magenta')
    table.add_column('Rank', style='dim', width=6)
    table.add_column('Filename')
    table.add_column('Similarity', justify='right')
    table.add_column('Preview')

    for i, result in enumerate(results, start=1):
        filename = result['metadata']['filename']
        similarity = f"{result['similarity']:.3f}"
        preview = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
        
        table.add_row(str(i), filename, similarity, preview)

    console.print(table)
    
    # Save results to file
    if output_file:
        with open(output_file, 'w') as f:
            for result in results:
                f.write(result['content'] + "\n\n")
        console.print(f"\n[green]Results saved to {output_file}[/green]")


if __name__ == '__main__':
    query_interface()
