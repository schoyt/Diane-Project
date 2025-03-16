"""
hybrid_search.py - Implements hybrid search combining SQL date filtering with vector semantic search
"""

from sqlalchemy import create_engine, and_, or_, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import re
import json
import os

class HybridSearch:
    def __init__(self, sql_db_path, vector_store, sql_model):
        """
        Initialize hybrid search with connections to both databases
        
        Args:
            sql_db_path: Path to the SQLite database
            vector_store: ChromaDB vector store instance
            sql_model: SQLAlchemy model for transcript metadata
        """
        self.engine = create_engine(f"sqlite:///{sql_db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.vector_store = vector_store
        self.sql_model = sql_model
        
    def parse_date_filter(self, date_str):
        """
        Parse date strings into datetime objects
        
        Args:
            date_str: String representation of date (e.g., "October 5, 2023")
            
        Returns:
            tuple: (start_date, end_date) as datetime objects
        """
        # Handle relative date terms
        today = datetime.now()
        
        # Yesterday
        if re.match(r"yesterday|last\s+day", date_str, re.IGNORECASE):
            target_date = today - timedelta(days=1)
            return target_date.replace(hour=0, minute=0, second=0), target_date.replace(hour=23, minute=59, second=59)
        
        # Last week
        elif re.match(r"last\s+week", date_str, re.IGNORECASE):
            start_date = today - timedelta(days=7)
            return start_date, today
        
        # Last month
        elif re.match(r"last\s+month", date_str, re.IGNORECASE):
            start_date = today - timedelta(days=30)
            return start_date, today
            
        # Last year
        elif re.match(r"last\s+year", date_str, re.IGNORECASE):
            start_date = today - timedelta(days=365)
            return start_date, today
            
        # Try to parse specific date formats
        try:
            # Try common date formats
            for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.replace(hour=0, minute=0, second=0), parsed_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    continue
                    
            # Try month and year
            for fmt in ["%B %Y", "%b %Y"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    last_day = 28
                    if parsed_date.month in [1, 3, 5, 7, 8, 10, 12]:
                        last_day = 31
                    elif parsed_date.month in [4, 6, 9, 11]:
                        last_day = 30
                    return parsed_date.replace(day=1, hour=0, minute=0, second=0), parsed_date.replace(day=last_day, hour=23, minute=59, second=59)
                except ValueError:
                    continue
                    
            # Try just month
            for fmt in ["%B", "%b"]:
                try:
                    this_year = today.year
                    month_str = f"{date_str} {this_year}"
                    parsed_date = datetime.strptime(month_str, f"{fmt} %Y")
                    last_day = 28
                    if parsed_date.month in [1, 3, 5, 7, 8, 10, 12]:
                        last_day = 31
                    elif parsed_date.month in [4, 6, 9, 11]:
                        last_day = 30
                    return parsed_date.replace(day=1, hour=0, minute=0, second=0), parsed_date.replace(day=last_day, hour=23, minute=59, second=59)
                except ValueError:
                    continue
                
            # Return None if we can't parse the date
            return None, None
            
        except Exception:
            return None, None
            
    def search(self, query_params, max_results=10):
        """
        Perform hybrid search using SQL for date filtering and vector DB for semantic search
        
        Args:
            query_params: QueryParameters object with parsed query information
            max_results: Maximum number of results to return
            
        Returns:
            list: List of search results with transcript content and metadata
        """
        session = self.Session()
        try:
            # Step 1: Filter by date in SQL if date filters are provided
            sql_query = session.query(self.sql_model)
            date_filtered = False
            
            if query_params.date_filters:
                date_conditions = []
                
                for date_str in query_params.date_filters:
                    start_date, end_date = self.parse_date_filter(date_str)
                    if start_date and end_date:
                        date_filtered = True
                        date_conditions.append(
                            and_(
                                self.sql_model.timestamp >= start_date,
                                self.sql_model.timestamp <= end_date
                            )
                        )
                
                if date_conditions:
                    sql_query = sql_query.filter(or_(*date_conditions))
            
            # Step 2: Get the IDs from SQL query
            if date_filtered:
                sql_results = sql_query.all()
                document_ids = [str(result.id) for result in sql_results]
                
                # If no SQL results found, return empty list
                if not document_ids:
                    return []
            else:
                document_ids = None
            
            # Step 3: Perform semantic search in vector DB
            search_text = " ".join(query_params.keywords) if query_params.keywords else "memory"
            
            # If we have document IDs from SQL filtering, use them to constrain vector search
            if document_ids:
                results = self.vector_store.similarity_search(
                    search_text,
                    k=max_results,
                    filter={"id": {"$in": document_ids}}
                )
            else:
                # No date filtering, just do semantic search
                results = self.vector_store.similarity_search(
                    search_text,
                    k=max_results
                )
            
            # Step 4: Format results
            formatted_results = []
            for result in results:
                # Extract transcript content
                content = result.page_content
                
                # Get metadata (timestamp, file path, etc.)
                metadata = result.metadata
                
                # If we have matching SQL records, add any additional metadata
                if date_filtered:
                    for sql_result in sql_results:
                        if str(sql_result.id) == metadata.get("id", ""):
                            # Add additional metadata from SQL
                            for key, value in sql_result.__dict__.items():
                                if not key.startswith("_") and key != "id":
                                    metadata[key] = value
                
                formatted_results.append({
                    "content": content,
                    "metadata": metadata,
                    "score": getattr(result, "score", None)  # Some vector stores provide score
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error in hybrid search: {str(e)}")
            return []
        finally:
            session.close()
    
    def count_query(self, query_params):
        """
        Process count-type queries
        
        Args:
            query_params: QueryParameters object with parsed query information
            
        Returns:
            dict: Count results with context
        """
        session = self.Session()
        try:
            # For keyword frequency counting
            if query_params.keywords:
                # Get base query from SQL
                sql_query = session.query(self.sql_model)
                
                # Apply date filters if available
                if query_params.date_filters:
                    date_conditions = []
                    
                    for date_str in query_params.date_filters:
                        start_date, end_date = self.parse_date_filter(date_str)
                        if start_date and end_date:
                            date_conditions.append(
                                and_(
                                    self.sql_model.timestamp >= start_date,
                                    self.sql_model.timestamp <= end_date
                                )
                            )
                    
                    if date_conditions:
                        sql_query = sql_query.filter(or_(*date_conditions))
                
                # Get all matching records
                results = sql_query.all()
                
                # Count occurrences of keywords in transcripts
                keyword_counts = {keyword: 0 for keyword in query_params.keywords}
                matching_dates = []
                
                for result in results:
                    # Load the full transcript
                    try:
                        transcript_path = result.file_path
                        if os.path.exists(transcript_path):
                            with open(transcript_path, 'r') as f:
                                transcript_text = f.read().lower()
                                
                            # Count occurrences of each keyword
                            for keyword in query_params.keywords:
                                count = transcript_text.count(keyword.lower())
                                if count > 0:
                                    keyword_counts[keyword] += count
                                    matching_dates.append(result.timestamp.strftime("%Y-%m-%d"))
                    except Exception as e:
                        print(f"Error reading transcript {result.file_path}: {str(e)}")
                
                return {
                    "type": "keyword_count",
                    "counts": keyword_counts,
                    "total_mentions": sum(keyword_counts.values()),
                    "matching_dates": sorted(list(set(matching_dates))),
                    "date_range": query_params.time_range if query_params.time_range else "all time"
                }
            
            return {
                "type": "error",
                "message": "No keywords provided for counting"
            }
            
        except Exception as e:
            print(f"Error in count query: {str(e)}")
            return {
                "type": "error",
                "message": f"Error processing count query: {str(e)}"
            }
        finally:
            session.close()