# Adding Documents to Your Database

## Quick Reference

### 1. Add Files
Copy your documents to the documents folder:
```bash
cp /path/to/your/document.pdf ./data/documents/
```

### 2. Process Documents
Run the processing script:
```bash
./process_new_documents.py
```

### 3. Done!
Your documents are now indexed and searchable.

## Supported File Types
- **Text files**: `.txt`
- **PDFs**: `.pdf`
- **Word documents**: `.doc`, `.docx`
- **Spreadsheets**: `.csv`

## Processing Options

### Standard Processing (Recommended)
Processes only new/changed documents:
```bash
./process_new_documents.py
```

### Full Rebuild
Clears everything and processes all documents:
```bash
./process_new_documents.py --clear --force
```

### Interactive Mode
Asks before clearing existing data:
```bash
./process_new_documents.py --clear
```

## What Gets Created

When you process documents, the system creates:

1. **Text chunks** - Documents split into searchable pieces
2. **Vector embeddings** - Mathematical representations for similarity search
3. **Metadata database** - File information, processing dates, etc.
4. **Theological index** - Index of theological concepts (if applicable)
5. **Scripture index** - Index of Bible references (if applicable)

## Monitoring

### Check Processing Logs
```bash
tail -f logs/document_processing.log
```

### View Database Stats
Your document count and chunk information are displayed after processing.

## Troubleshooting

### File Too Large
- Maximum file size: 100MB
- Split large files or contact admin to increase limit

### Unsupported Format
- Convert to supported format (.txt, .pdf, .doc, .docx, .csv)
- Or request support for additional formats

### Processing Errors
- Check `logs/document_processing.log` for detailed error messages
- Ensure you have sufficient disk space and memory
- Verify Ollama is running if using LLM features

## Tips

- **Organize files**: Use descriptive filenames for better searchability
- **Batch processing**: Add multiple files at once for efficiency  
- **Regular updates**: Run processing after adding new documents
- **Backup**: Keep originals safe - the system processes copies
