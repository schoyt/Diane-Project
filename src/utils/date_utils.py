"""
date_utils.py - Helper functions for date parsing and manipulation
"""

import re
from datetime import datetime, timedelta

def parse_natural_date(date_str):
    """
    Parse a natural language date string into a datetime object
    
    Args:
        date_str: String representation of date (e.g., "October 5, 2023")
        
    Returns:
        tuple: (start_date, end_date, is_range) as datetime objects and boolean
    """
    today = datetime.now()
    is_range = False

    # Yesterday
    if re.match(r"yesterday|last\s+day", date_str, re.IGNORECASE):
        target_date = today - timedelta(days=1)
        is_range = True
        return (
            target_date.replace(hour=0, minute=0, second=0), 
            target_date.replace(hour=23, minute=59, second=59),
            is_range
        )

    # Last week
    elif re.match(r"last\s+week", date_str, re.IGNORECASE):
        start_date = today - timedelta(days=7)
        is_range = True
        return start_date, today, is_range

    # Last month
    elif re.match(r"last\s+month", date_str, re.IGNORECASE):
        start_date = today - timedelta(days=30)
        is_range = True
        return start_date, today, is_range
        
    # Last year
    elif re.match(r"last\s+year", date_str, re.IGNORECASE):
        start_date = today - timedelta(days=365)
        is_range = True
        return start_date, today, is_range
        
    # Try to parse specific date formats
    try:
        # Try common date formats
        for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return (
                    parsed_date.replace(hour=0, minute=0, second=0), 
                    parsed_date.replace(hour=23, minute=59, second=59),
                    False
                )
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
                is_range = True
                return (
                    parsed_date.replace(day=1, hour=0, minute=0, second=0), 
                    parsed_date.replace(day=last_day, hour=23, minute=59, second=59),
                    is_range
                )
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
                is_range = True
                return (
                    parsed_date.replace(day=1, hour=0, minute=0, second=0), 
                    parsed_date.replace(day=last_day, hour=23, minute=59, second=59),
                    is_range
                )
            except ValueError:
                continue
            
        # Return None if we can't parse the date
        return None, None, False
        
    except Exception:
        return None, None, False

def format_timestamp(timestamp, include_time=True):
    """
    Format a timestamp in a human-readable format
    
    Args:
        timestamp: datetime object
        include_time: Whether to include the time in the output
        
    Returns:
        str: Formatted timestamp
    """
    if include_time:
        return timestamp.strftime("%B %d, %Y at %I:%M %p")
    else:
        return timestamp.strftime("%B %d, %Y")

def get_date_range_description(start_date, end_date):
    """
    Get a human-readable description of a date range
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        
    Returns:
        str: Human-readable date range description
    """
    if start_date.date() == end_date.date():
        return format_timestamp(start_date, include_time=False)
        
    # Same month and year
    if start_date.month == end_date.month and start_date.year == end_date.year:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%d, %Y')}"
        
    # Same year
    if start_date.year == end_date.year:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
        
    # Different years
    return f"{format_timestamp(start_date, include_time=False)} - {format_timestamp(end_date, include_time=False)}"

def is_date_in_range(timestamp, start_date, end_date):
    """
    Check if a timestamp is within a date range
    
    Args:
        timestamp: datetime to check
        start_date: Start of range
        end_date: End of range
        
    Returns:
        bool: True if timestamp is within range
    """
    return start_date <= timestamp <= end_date