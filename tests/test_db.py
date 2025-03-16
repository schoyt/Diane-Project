# tests/test_db.py
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

# Add the src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database.sql_db import DatabaseManager

def test_database():
    """Test database functionality"""
    print("Testing database connection and operations...")
    
    # Initialize database connection
    db = DatabaseManager()
    
    # Test data
    today = date.today()
    yesterday = today - timedelta(days=1)
    test_transcript = "This is a test transcript for the Diane project. I talked about work, vacation, and family today."
    
    try:
        # 1. Test transcript insertion
        keywords = ["test", "project", "diane", "work", "vacation", "family"]
        transcript_id = db.insert_transcript(
            filename="test_recording.mp3",
            recording_date=today,
            transcript_text=test_transcript,
            keywords=keywords
        )
        print(f"✓ Inserted test transcript with ID: {transcript_id}")
        
        # 2. Test keyword update
        new_keywords = {"important": 1}  # Adding a new keyword
        db.add_keywords(transcript_id, new_keywords)
        print(f"✓ Updated keywords for transcript")
        
        # 3. Test date query
        date_results = db.query_by_date(today)
        print(f"✓ Found {len(date_results)} transcripts for today")
        
        # 4. Test keyword query
        keyword_results = db.query_by_keyword("vacation")
        print(f"✓ Found {len(keyword_results)} transcripts mentioning 'vacation'")
        
        # 5. Test keyword counting
        vacation_count = db.count_keyword_mentions("vacation")
        print(f"✓ 'vacation' mentioned in {vacation_count} transcripts")
        
        # 6. Test top keywords
        top_keywords = db.get_top_keywords(limit=5)
        print(f"✓ Top keywords: {top_keywords}")
        
        # 7. Test text search
        text_results = db.search_transcript_text("family")
        print(f"✓ Found {len(text_results)} transcripts containing 'family'")
        
        print("\nAll database tests completed successfully!")
        
    except Exception as e:
        print(f"× Test failed: {e}")

if __name__ == "__main__":
    test_database()