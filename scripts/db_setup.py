import os
import sys
from pathlib import Path
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.sql_db import DatabaseManager

def setup_database():
    """Sets up the SQLite database for the Diane project."""
    print("Setting up SQLite database...")
    
    # Create data directory if it doesn't exist
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Path to the SQLite database file
    db_path = data_dir / "diane_db.sqlite"
    
    # Initialize database manager
    db = DatabaseManager(db_path)
    
    # Create database schema
    db.init_db()
    
    print("SQLite database setup complete!")

if __name__ == "__main__":
    setup_database()