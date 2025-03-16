# tests/test_workflow.py
import sys
import os
from pathlib import Path
from datetime import datetime, date

# Add the src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processing.transcribe import transcribe_audio, process_audio
from processing.metadata_extractor import extract_metadata, process_transcript
from database.sql_db import DatabaseManager

def test_full_workflow():
    """Test the entire workflow from audio transcription to database storage"""
    print("Testing full transcript processing workflow...")
    
    # Ensure test directories exist
    os.makedirs("data/raw_audio", exist_ok=True)
    os.makedirs("data/transcripts", exist_ok=True)
    os.makedirs("data/processed_audio", exist_ok=True)
    
    # Initialize database
    db = DatabaseManager()
    db.init_db()
    
    # Path to a test audio file (you'll need to provide this)
    test_audio = "data/raw_audio/test_recording.mp3"
    
    try:
        # Step 1: Check if test file exists
        if not os.path.exists(test_audio):
            print(f"× Test audio file not found at {test_audio}")
            print("Please add a test audio file and run again.")
            return
        
        # Step 2: Transcribe audio
        print("Transcribing test audio...")
        transcript = transcribe_audio(test_audio)
        print(f"✓ Generated transcript: {transcript[:50]}...")
        
        # Step 3: Save transcript to file
        transcript_filename = f"{Path(test_audio).stem}.txt"
        transcript_path = os.path.join("data", "transcripts", transcript_filename)
        
        with open(transcript_path, "w") as f:
            f.write(transcript)
        print(f"✓ Saved transcript to {transcript_path}")
        
        # Step 4: Extract metadata
        print("Extracting metadata...")
        metadata = extract_metadata(Path(test_audio).name, transcript)
        print(f"✓ Extracted metadata: date={metadata['date']}, {len(metadata['keywords'])} keywords")
        
        # Step 5: Save to database
        print("Storing in database...")
        
        # Convert date string to date object
        recording_date = None
        if metadata['date']:
            recording_date = datetime.fromisoformat(metadata['date']).date()
        else:
            recording_date = date.today()
        
        # Insert transcript
        transcript_id = db.insert_transcript(
            filename=Path(test_audio).name,
            recording_date=recording_date,
            transcript_text=transcript,
            keywords=metadata['keywords']
        )
        
        print(f"✓ Stored in database with ID: {transcript_id}")
        
        # Step 6: Test retrieval
        print("Testing retrieval...")
        results = db.query_by_date(recording_date)
        
        if results and len(results) > 0:
            print(f"✓ Successfully retrieved transcript from database")
        else:
            print(f"× Failed to retrieve transcript from database")
        
        print("\nFull workflow test completed!")
        
    except Exception as e:
        print(f"× Test failed: {e}")

if __name__ == "__main__":
    test_full_workflow()