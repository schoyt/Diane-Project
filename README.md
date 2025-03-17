# Diane: AI-Personal Memory Assistant

Voice-based AI assistant that uses natural language to query transcribed audio recordings of daily thoughts and activities.

## Features

- Audio to text transcription using Faster Whisper
- Natural language queries using LangChain and OpenAI
- Dual database system (SQL + Vector DB)
- Hybrid search combining date filtering and semantic search

## Project Structure

Diane/
├── config/                 # Settings/API keys
│   ├── settings.yaml       # Configuration settings
│   └── .env                # API keys (OPENAI_API_KEY, etc.) loaded with python-dotenv
│
├── data/                   # Storage for all data
│   ├── diane.db            # Main SQLite database file
│   ├── diane_db.sqlite     # Alternative SQLite database file
│   │
│   ├── database/           # Structured storage
│   │   └── vector_store/   # ChromaDB embeddings directory
│   │       ├── chroma.sqlite3  # ChromaDB SQLite database
│   │       └── c423fff5-f2e0-4feb-9dbb-458e3d49c993/  # ChromaDB data directory
│   │           ├── data_level0.bin    # ChromaDB vector data
│   │           ├── header.bin         # ChromaDB header information
│   │           ├── length.bin         # ChromaDB length information
│   │           └── link_lists.bin     # ChromaDB linking information
│   │
│   ├── processed_audio/    # Directory for processed audio files
│   │
│   ├── raw_audio/          # Original voice recordings
│   │   ├── test_recording.mp3  # Main test recording file
│   │   └── test_audio/     # Test audio directory
│   │       └── voicemail-12909891136.m4a  # Sample voicemail test file
│   │
│   └── transcripts/        # Whisper-generated text files
│       ├── 250206_1156.txt             # Transcription file
│       ├── 250206_1156_metadata.json   # Metadata for transcription
│       ├── test_recording.txt          # Transcription of test recording
│       └── transcript2025-02-07/       # Organized transcripts by date
│
├── scripts/                # One-off utilities
│   ├── db_setup.py         # Initialize databases
│   └── test_chroma.py      # Testing ChromaDB functionality
│
├── src/                    # Source code
│   ├── __init__.py         # Init file for src module
│   │
│   ├── chains/             # LangChain workflows
│   │   ├── __init__.py     # Init file for chains module
│   │   ├── hybrid_search.py        # Combines SQL and vector search
│   │   ├── query_parser.py         # Parses natural language queries
│   │   └── retrieval_chain.py      # LangChain retrieval implementation
│   │
│   ├── database/           # DB interactions
│   │   ├── __init__.py     # Init file for database module
│   │   ├── sql_db.py       # SQLAlchemy implementation
│   │   └── vector_db.py    # ChromaDB implementation with langchain-chroma
│   │
│   ├── processing/         # Audio → text pipeline
│   │   ├── __init__.py     # Init file for processing module
│   │   ├── db_integration.py       # Database integration logic
│   │   ├── metadata_extractor.py   # Using spaCy for keyword extraction
│   │   └── transcribe.py           # Using Faster Whisper for transcription
│   │
│   └── utils/              # Helper functions
│       ├── __init__.py     # Init file for utils module
│       └── date_utils.py   # Date handling utilities
│
├── tests/                  # Unit/integration tests
│   ├── test_db.py          # Database testing
│   ├── test_query_system.py    # Tests for query functionality
│   └── test_workflow.py    # Tests for overall workflow
│
├── app.py                  # Main CLI/GUI/API entrypoint
├── requirements.txt        # Python dependencies
├── README.md               # Project docs
└── .gitignore              # Git ignore file

## Setup Instructions

[Basic setup steps]
