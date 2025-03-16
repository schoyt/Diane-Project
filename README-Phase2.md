# Diane Project: Phase 2 - Query System

This document provides an overview of the query system components created in Phase 2 of the Diane project.

## Components Created

1. **Retrieval Chain** (`src/chains/retrieval_chain.py`)

   - Implements LangChain retrieval chain for querying transcript data
   - Uses ChatOpenAI for generating responses based on retrieved context
   - Supports adding new documents to the vector store

2. **Query Parser** (`src/chains/query_parser.py`)

   - Parses natural language queries to extract dates, keywords, and query intent
   - Uses both LLM and spaCy for robust parsing
   - Classifies queries into "recall", "count", "insight", or "general" types

3. **Hybrid Search** (`src/chains/hybrid_search.py`)

   - Combines SQL date filtering with ChromaDB vector semantic search
   - Supports filtering by date ranges
   - Handles count queries for keyword frequency

4. **Date Utilities** (`src/utils/date_utils.py`)

   - Helper functions for date parsing and manipulation
   - Parses natural language date expressions
   - Formats timestamps in a human-readable way

5. **Configuration** (`config/settings.yaml`)

   - Central configuration file for all project components
   - Settings for audio processing, transcription, databases, and LLM

6. **Updated Application** (`app.py`)
   - Command-line interface for interacting with Diane
   - Supports processing audio files and querying memories
   - Provides an interactive mode for ongoing conversations

## How to Use

### Processing Audio

```bash
python app.py process path/to/audio_file.mp3
```

This will:

1. Transcribe the audio using Faster Whisper
2. Extract metadata (keywords, dates) from the transcript
3. Store the data in both SQL and vector databases

### Querying Memories

```bash
python app.py query "What did I talk about yesterday?"
```

This will:

1. Parse the natural language query
2. Perform hybrid search of your memories
3. Generate a relevant response using LangChain and OpenAI

### Interactive Mode

```bash
python app.py interactive
```

This launches an interactive session where you can chat with Diane and ask multiple questions.

## Query Types Supported

1. **Recall Queries**

   - "What did I talk about on October 5th?"
   - "Tell me about my conversation regarding vacation plans."

2. **Count Queries**

   - "How many times did I mention 'meeting' last week?"
   - "Count the number of times I talked about John."

3. **Insight Queries**

   - "What patterns do you notice in my productivity discussions?"
   - "Find insights about my project planning from June."

4. **General Queries**
   - "What are my most common topics?"
   - "Summarize my thoughts on machine learning."

## Next Steps

After implementing Phase 2, the project now has a functioning query system. The next phases will focus on:

1. **Phase 3: Validation**

   - Test with sample recordings and queries
   - Implement bulk ingest for existing audio

2. **Phase 4: Interface**

   - Add voice response capability
   - Enhance the CLI interface

3. **Phase 5: Enhancements**
   - Implement analytics for trends
   - Add auto-tagging for emotions and entities
   - Build GUI/web interface
