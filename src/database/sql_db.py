import os
import sqlite3
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for the Diane project using SQLite"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database manager
        
        Args:
            db_path: Path to SQLite database file (default: data/diane.db)
        """
        if db_path is None:
            # Use project root to ensure consistent path resolution
            project_root = Path(__file__).parent.parent.parent
            db_folder = project_root / "data"
            db_folder.mkdir(exist_ok=True)
            db_path = str(db_folder / "diane.db")
        
        self.db_path = db_path
        self.config = {"database": db_path}
        logger.info(f"Database configured at: {db_path}")
    
    def connect(self):
        """
        Connect to the SQLite database
        
        Returns:
            sqlite3.Connection: Database connection
        """
        try:
            # Enable foreign key constraints
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            # Return dictionary-like rows
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_db(self):
        """
        Initialize the database schema
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    recording_date DATE NOT NULL,
                    transcript_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds INTEGER,
                    file_path TEXT,
                    transcript_text TEXT,
                    word_count INTEGER
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    UNIQUE(transcript_id, keyword)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    UNIQUE(transcript_id, key)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE CASCADE,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding_vector BLOB,
                    UNIQUE(transcript_id, chunk_index)
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_recording_date ON transcripts(recording_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_key_value ON metadata(key, value);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_transcript_id ON embeddings(transcript_id);")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()
    
    def insert_transcript(self, filename: str, recording_date: datetime, 
                         transcript_text: str, keywords: List[str] = None,
                         duration_seconds: int = None, file_path: str = None) -> int:
        """
        Insert a transcript into the database
        
        Args:
            filename: Original audio file name
            recording_date: Date of the recording
            transcript_text: Full transcript text
            keywords: List of keywords extracted from the transcript
            duration_seconds: Duration of the audio in seconds (optional)
            file_path: Path to the transcript file (optional)
            
        Returns:
            int: ID of the inserted transcript record
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Format date properly for SQLite
            if isinstance(recording_date, datetime):
                recording_date = recording_date.date()
            
            if isinstance(recording_date, date):
                recording_date = recording_date.isoformat()
            
            # Calculate word count
            word_count = len(transcript_text.split()) if transcript_text else 0
            
            # Insert transcript
            cursor.execute("""
                INSERT INTO transcripts 
                (filename, recording_date, transcript_text, word_count, duration_seconds, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filename, recording_date, transcript_text, word_count, duration_seconds, file_path))
            
            transcript_id = cursor.lastrowid
            
            # Insert keywords
            if keywords:
                # Count frequency of each keyword
                keyword_counts = {}
                for keyword in keywords:
                    keyword = keyword.lower()
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                # Insert each unique keyword with its frequency
                for keyword, frequency in keyword_counts.items():
                    cursor.execute("""
                        INSERT INTO keywords (transcript_id, keyword, frequency)
                        VALUES (?, ?, ?)
                    """, (transcript_id, keyword, frequency))
            
            conn.commit()
            logger.info(f"Inserted transcript: {filename} with ID {transcript_id}")
            return transcript_id
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error inserting transcript: {e}")
            raise
        finally:
            conn.close()
    
    def query_by_date(self, date_value: date) -> List[Dict[str, Any]]:
        """
        Query transcripts by recording date
        
        Args:
            date_value: Date to query
            
        Returns:
            List of transcript records
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Format date for SQLite
            if isinstance(date_value, date):
                date_value = date_value.isoformat()
            
            cursor.execute("""
                SELECT t.*, GROUP_CONCAT(k.keyword) as keywords
                FROM transcripts t
                LEFT JOIN keywords k ON t.id = k.transcript_id
                WHERE t.recording_date = ?
                GROUP BY t.id
            """, (date_value,))
            
            results = []
            for row in cursor.fetchall():
                # Convert row to dict
                result = dict(row)
                
                # Split keywords into a list
                if result.get('keywords'):
                    result['keywords'] = result['keywords'].split(',')
                else:
                    result['keywords'] = []
                
                results.append(result)
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error querying transcripts by date: {e}")
            raise
        finally:
            conn.close()
    
    def search_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search transcripts by keyword or content
        
        Args:
            query: Search term
            
        Returns:
            List of matching transcript records
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Use SQLite FTS if available or fall back to LIKE
            search_term = f"%{query}%"
            
            cursor.execute("""
                SELECT t.*, GROUP_CONCAT(k.keyword) as keywords
                FROM transcripts t
                LEFT JOIN keywords k ON t.id = k.transcript_id
                WHERE t.transcript_text LIKE ?
                   OR EXISTS (SELECT 1 FROM keywords WHERE transcript_id = t.id AND keyword LIKE ?)
                GROUP BY t.id
                ORDER BY t.recording_date DESC
            """, (search_term, search_term))
            
            results = []
            for row in cursor.fetchall():
                # Convert row to dict
                result = dict(row)
                
                # Split keywords into a list
                if result.get('keywords'):
                    result['keywords'] = result['keywords'].split(',')
                else:
                    result['keywords'] = []
                
                results.append(result)
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error searching transcripts: {e}")
            raise
        finally:
            conn.close()


# Helper function for setting up the database (previously in db_setup.py)
def setup_database():
    """Sets up the SQLite database for the Diane project."""
    print("Setting up SQLite database...")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Create database schema
    db.init_db()
    
    print("SQLite database setup complete!")


# Allow running this file directly to set up the database
if __name__ == "__main__":
    setup_database()