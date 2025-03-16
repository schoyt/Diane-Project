# src/processing/db_integration.py
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.sql_db import DatabaseManager

def save_to_database(transcript_path: str, metadata: Dict[str, Any] = None) -> int:
    """
    Save a transcript and its metadata to the database
    
    Args:
        transcript_path: Path to the transcript file
        metadata: Metadata dictionary (optional)
        
    Returns:
        int: ID of the inserted transcript record
    """
    # Read transcript
    with open(transcript_path, 'r') as f:
        transcript_text = f.read()
    
    # Get metadata if not provided
    if metadata is None:
        metadata_path = os.path.splitext(transcript_path)[0] + "_metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            # Default metadata
            filename = os.path.basename(transcript_path)
            metadata = {
                "date": datetime.now().date().isoformat(),
                "keywords": []
            }
    
    # Connect to database
    db = DatabaseManager()
    
    # Insert transcript
    transcript_id = db.insert_transcript(
        filename=os.path.basename(transcript_path),
        recording_date=datetime.fromisoformat(metadata["date"]),
        transcript_text=transcript_text,
        keywords=metadata["keywords"]
    )
    
    return transcript_id

def process_directory(directory_path: str) -> None:
    """
    Process all transcript files in a directory
    
    Args:
        directory_path: Path to the directory containing transcript files
    """
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt") and not filename.endswith("_metadata.txt"):
            transcript_path = os.path.join(directory_path, filename)
            try:
                transcript_id = save_to_database(transcript_path)
                print(f"Added transcript {filename} to database with ID: {transcript_id}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Process specific file or directory
        path = sys.argv[1]
        if os.path.isfile(path) and path.endswith(".txt"):
            save_to_database(path)
        elif os.path.isdir(path):
            process_directory(path)
        else:
            print("Please provide a valid transcript file (.txt) or directory")
    else:
        print("Usage: python db_integration.py <transcript_file_or_directory>")