"""
date_utils.py - Helper functions for date parsing and manipulation
"""

import re
from datetime import datetime, timedelta

def parse_natural_date(date_str):
    """
    Parse a natural language date string into a datetime object
    
    Args:
        date_str: Natural language date string (e.g., 'yesterday', 'last week', 'October 5')
        
    Returns:
        tuple: (start_datetime, end_datetime, is_range)
    """
    today = datetime.now()
    
    # Handle 'today'
    if re.match(r'^today$', date_str, re.IGNORECASE):
        return (
            today.replace(hour=0, minute=0, second=0, microsecond=0),
            today.replace(hour=23, minute=59, second=59, microsecond=999999),
            False
        )
    
    # Handle 'yesterday'
    if re.match(r'^yesterday$', date_str, re.IGNORECASE):
        yesterday = today - timedelta(days=1)
        return (
            yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
            yesterday.replace(hour=23, minute=59, second=59, microsecond=999999),
            False
        )
    
    # Handle 'last week'
    if re.match(r'^last\s+week$', date_str, re.IGNORECASE):
        start_date = today - timedelta(days=7)
        return (
            start_date.replace(hour=0, minute=0, second=0, microsecond=0),
            today.replace(hour=23, minute=59, second=59, microsecond=999999),
            True
        )
    
    # Handle 'last month'
    if re.match(r'^last\s+month$', date_str, re.IGNORECASE):
        start_date = today - timedelta(days=30)
        return (
            start_date.replace(hour=0, minute=0, second=0, microsecond=0),
            today.replace(hour=23, minute=59, second=59, microsecond=999999),
            True
        )
    
    # Handle 'last year'
    if re.match(r'^last\s+year$', date_str, re.IGNORECASE):
        start_date = today - timedelta(days=365)
        return (
            start_date.replace(hour=0, minute=0, second=0, microsecond=0),
            today.replace(hour=23, minute=59, second=59, microsecond=999999),
            True
        )
    
    # Try to parse specific dates
    for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return (
                parsed_date.replace(hour=0, minute=0, second=0, microsecond=0),
                parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999),
                False
            )
        except ValueError:
            continue
    
    # Try to parse month and year
    for fmt in ["%B %Y", "%b %Y"]:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            
            # Determine last day of month
            if parsed_date.month in [1, 3, 5, 7, 8, 10, 12]:
                last_day = 31
            elif parsed_date.month in [4, 6, 9, 11]:
                last_day = 30
            elif parsed_date.month == 2:
                # Crude leap year check
                if parsed_date.year % 4 == 0 and (parsed_date.year % 100 != 0 or parsed_date.year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 28
                
            return (
                parsed_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                parsed_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999),
                True
            )
        except ValueError:
            continue
    
    # Try to parse just month (assume current year)
    for fmt in ["%B", "%b"]:
        try:
            current_year = today.year
            month_str = f"{date_str} {current_year}"
            parsed_date = datetime.strptime(month_str, f"{fmt} %Y")
            
            # Determine last day of month
            if parsed_date.month in [1, 3, 5, 7, 8, 10, 12]:
                last_day = 31
            elif parsed_date.month in [4, 6, 9, 11]:
                last_day = 30
            elif parsed_date.month == 2:
                # Crude leap year check
                if parsed_date.year % 4 == 0 and (parsed_date.year % 100 != 0 or parsed_date.year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 28
                
            return (
                parsed_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                parsed_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999),
                True
            )
        except ValueError:
            continue
    
    # Could not parse the date
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