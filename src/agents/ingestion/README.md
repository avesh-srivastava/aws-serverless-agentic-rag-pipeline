# Data Ingestion Agent

## Overview
The Data Ingestion Agent is responsible for processing raw documents (PDFs, CSVs) and converting them into searchable knowledge base entries.

## Lambda Functions
- **aai_start_textract.py** - Initiates PDF text extraction
- **aai_check_textract_status.py** - Monitors extraction completion
- **aai_preprocess_csv.py** - Processes CSV data
- **aai_chunk_text.py** - Splits text into manageable chunks
- **aai_generate_embeddings.py** - Creates vector embeddings
- **aai_store_opensearch.py** - Stores data in OpenSearch
- **aai_create_opensearch_index.py** - Sets up search index

## Capabilities
- PDF text extraction using AWS Textract
- CSV data preprocessing and cleaning
- Text chunking for optimal embedding
- Vector embedding generation via Bedrock
- OpenSearch index management