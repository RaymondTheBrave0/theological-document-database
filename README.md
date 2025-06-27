# Document Database Project

This project aims to create a comprehensive document management system using Python and Ollama. The system will handle multiple document formats and provide both terminal and web-based query interfaces.

## Requirements

1. **Document Processing:**
   - Support for DOC, DOCX, PDF, CSV, TXT formats
   - Efficient handling of large files

2. **Database and Storage:**
   - Use a vector database to store document embeddings
   - Deduplication support to avoid storing the same information multiple times

3. **LLM Integration:**
   - Use Ollama for local language generation, ensuring no data is used to answer questions unless explicitly stored

4. **User Interfaces:**
   - Terminal Interface: Professional CLI with text editing
   - Web Interface: Easy-to-use GUI

5. **System Performance:**
   - Utilize GPU, RAM, and multi-core processing

6. **Portability:**
   - Cross-platform compatibility with a focus on Linux, Windows, and macOS

## Project Structure

- **src**: Source code for the project
- **data**: Folder for input documents
- **output**: Folder for query results
- **web**: Web GUI files
- **process_new_documents.py**: Script to process new documents
- **merge_pdfs.py**: Utility to merge multiple PDF files into one
- **tests**: Test cases for the system

## Getting Started

### Quick Start Guide
1. **Setup Databases**: Use `./manage_databases.py list` to see available databases
2. **Process Documents**: `./process_new_documents.py --db-id 1001`
3. **Start Web Interface**: `./start_web.py --db-id 1001`
4. **Terminal Interface**: `./query_documents.py --db-id 1001` (if available)

### Multi-Database Usage
```bash
# List available databases
./manage_databases.py list

# Process documents for specific database
./process_new_documents.py --db-id 1003  # Eschatology

# Start web interface for specific database
./start_web.py --db-id 1003 --port 5001

# Multiple databases can run simultaneously on different ports
./start_web.py --db-id 1001 --port 5000  # Tim Warner Teaching
./start_web.py --db-id 1002 --port 5001  # General Christian Teaching
```

## Adding New Documents

### Quick Start
1. Copy your document files to `./data/documents/`
2. Run: `./process_new_documents.py`
3. Your documents are now searchable!

### Supported File Formats
- `.txt` - Plain text
- `.pdf` - PDF documents
- `.doc/.docx` - Microsoft Word documents
- `.csv` - Comma-separated values

### Processing Options

**Process new documents (incremental):**
```bash
./process_new_documents.py
```

**Clear all data and reprocess everything:**
```bash
./process_new_documents.py --clear --force
```

**Interactive mode (asks for confirmation):**
```bash
./process_new_documents.py --clear
```

### What Happens During Processing
1. **Text Extraction**: Extracts text from all supported file formats
2. **Chunking**: Splits documents into manageable chunks (1000 chars max, 200 char overlap)
3. **Embedding Generation**: Creates vector embeddings using sentence-transformers
4. **Database Storage**: Stores in both SQLite metadata DB and vector database
5. **Indexing**: Builds theological concept and scripture reference indexes
6. **Deduplication**: Prevents duplicate content storage

### File Limits
- Maximum file size: 100MB
- No limit on number of files
- Processing uses multi-core CPU and GPU acceleration when available

### Monitoring Progress
Check logs at `./logs/document_processing.log` for detailed processing information.

### 📖 For detailed instructions, see [ADDING_DOCUMENTS.md](./ADDING_DOCUMENTS.md)

## Web Interface

### Starting the Web Interface
```bash
# Start with default database
./start_web.py

# Start with specific database
./start_web.py --db-id 1003

# Custom host/port
./start_web.py --db-id 1001 --host 0.0.0.0 --port 8080

# List available databases
./start_web.py --list-databases
```

### Web Interface Features
- **Modern Bootstrap UI**: Clean, responsive interface
- **Database Selection**: Shows current database in navigation
- **AI-Powered Search**: Automatic AI responses (like terminal interface)
- **Auto-Save Results**: Query results automatically saved to files
- **Query History**: View recent searches
- **Real-time Interface**: Socket.IO for live updates
- **Export Functionality**: Save results in multiple formats

### Multiple Database Instances
You can run multiple web interfaces simultaneously:
```bash
# Terminal 1: Tim Warner Teaching on port 5000
./start_web.py --db-id 1001 --port 5000

# Terminal 2: Eschatology on port 5001  
./start_web.py --db-id 1003 --port 5001

# Terminal 3: Islamic End Times on port 5002
./start_web.py --db-id 1004 --port 5002
```

Access each database at:
- Tim Warner: http://localhost:5000
- Eschatology: http://localhost:5001  
- Islamic End Times: http://localhost:5002

## Utilities

### PDF Merger (merge_pdfs.py)

A utility script to merge multiple PDF files into a single document.

**Usage:**

```bash
# Merge specific PDF files
./merge_pdfs.py file1.pdf file2.pdf file3.pdf -o merged_output.pdf

# Merge all PDFs in a directory (with natural sorting)
./merge_pdfs.py -d /path/to/pdfs -o merged_output.pdf

# Use different sorting methods
./merge_pdfs.py -d /path/to/pdfs -s alphabetical -o output.pdf
./merge_pdfs.py -d /path/to/pdfs -s modified -o output.pdf

# Use file patterns
./merge_pdfs.py -d /path/to/pdfs -p "chapter*.pdf" -o book.pdf

# Skip pages with minimal content (header-only pages)
./merge_pdfs.py -d /path/to/pdfs --header-lines 2 -o clean_output.pdf
```

**Features:**
- Natural number sorting (file1.pdf, file2.pdf, file10.pdf)
- Multiple sorting options (natural, alphabetical, modification time)
- File pattern matching
- Progress reporting with page counts
- Error handling for corrupted PDFs
- Automatic output path resolution
- Header content filtering (skip pages with minimal content beyond headers)

**Header Removal:**
The `--header-lines` option removes the first N lines from each page:
- Simply skips the first N lines of text content from each page
- Useful for removing institutional headers, module names, etc.
- Preserves all remaining content exactly as it appears
- Example: `--header-lines 2` removes first 2 lines, keeps everything else

