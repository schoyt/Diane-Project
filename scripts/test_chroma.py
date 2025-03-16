"""
Test script for ChromaDB vector database functionality.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.database.vector_db import VectorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test ChromaDB functionality with sample data."""
    try:
        # Initialize vector database
        vector_db = VectorDatabase(db_directory="data/database/vector_store")
        logger.info("Vector database initialized successfully")
        
        # Sample transcript data
        sample_transcripts = [
            {
                "id": "transcript_20240301_1",
                "content": "Today I had a productive meeting about the Diane project. We discussed the implementation of ChromaDB and SQLite databases. I need to follow up with the team about API integration next week.",
                "metadata": {
                    "date": "2024-03-01",
                    "keywords": ["meeting", "productive", "Diane", "ChromaDB", "SQLite", "API"],
                    "emotion": "positive",
                    "source_file": "20240301_meeting.mp3"
                }
            },
            {
                "id": "transcript_20240302_1",
                "content": "I'm feeling stressed about the project deadlines. The vector database implementation is taking longer than expected. I should ask for help with the ChromaDB setup from the team.",
                "metadata": {
                    "date": "2024-03-02",
                    "keywords": ["stressed", "deadlines", "vector database", "ChromaDB", "help"],
                    "emotion": "negative",
                    "source_file": "20240302_notes.mp3"
                }
            },
            {
                "id": "transcript_20240305_1",
                "content": "Had coffee with Alex today. We talked about taking a vacation to Japan in the summer. Need to start researching flights and accommodations. Also mentioned the progress on the Diane project.",
                "metadata": {
                    "date": "2024-03-05",
                    "keywords": ["coffee", "Alex", "vacation", "Japan", "summer", "Diane"],
                    "emotion": "positive",
                    "source_file": "20240305_personal.mp3"
                }
            }
        ]
        
        # Add sample transcripts to the database
        for transcript in sample_transcripts:
            vector_db.add_transcript(
                transcript_id=transcript["id"],
                content=transcript["content"],
                metadata=transcript["metadata"]
            )
            
        logger.info(f"Added {len(sample_transcripts)} sample transcripts to vector database")
        
        # Test various search queries
        test_queries = [
            "What did I say about the Diane project?",
            "When did I mention feeling stressed?",
            "Tell me about vacation plans",
            "What happened on March 1st?"
        ]
        
        for query in test_queries:
            logger.info(f"\nExecuting search: '{query}'")
            results = vector_db.search(query, k=2)
            
            logger.info(f"Found {len(results)} results:")
            for i, doc in enumerate(results):
                logger.info(f"Result {i+1}:")
                logger.info(f"  Content: {doc.page_content[:100]}...")
                logger.info(f"  Metadata: {doc.metadata}")
                logger.info("---")
                
        # Test metadata filtering
        logger.info("\nTesting metadata filtering:")
        positive_results = vector_db.search(
            "What did I do?", 
            filter_metadata={"emotion": "positive"},
            k=3
        )
        
        logger.info(f"Found {len(positive_results)} results with positive emotion:")
        for i, doc in enumerate(positive_results):
            logger.info(f"Result {i+1}:")
            logger.info(f"  Content: {doc.page_content[:100]}...")
            logger.info(f"  Metadata: {doc.metadata}")
            logger.info("---")
            
        # Test retrieving specific transcript
        logger.info("\nTesting specific transcript retrieval:")
        specific_doc = vector_db.get_transcript("transcript_20240302_1")
        
        if specific_doc:
            logger.info(f"Retrieved transcript:")
            logger.info(f"  Content: {specific_doc.page_content}")
            logger.info(f"  Metadata: {specific_doc.metadata}")
        else:
            logger.error("Failed to retrieve specific transcript")
        
        logger.info("\nChromaDB test completed successfully")
        
    except Exception as e:
        logger.error(f"ChromaDB test failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()