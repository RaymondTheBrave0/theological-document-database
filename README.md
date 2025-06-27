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

- **Setup Environment**: Instructions to set up the development environment
- **Run Tests**: Instructions to execute test cases
- **Deployment**: Steps to deploy the application

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
```

**Features:**
- Natural number sorting (file1.pdf, file2.pdf, file10.pdf)
- Multiple sorting options (natural, alphabetical, modification time)
- File pattern matching
- Progress reporting with page counts
- Error handling for corrupted PDFs
- Automatic output path resolution

