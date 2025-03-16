"""
Tests for the query system components
"""

import unittest
import os
import sys
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from src.chains.query_parser import QueryParser, QueryParameters
from src.utils.date_utils import parse_natural_date, format_timestamp

class TestQueryParser(unittest.TestCase):
    def setUp(self):
        """Set up test case"""
        self.parser = QueryParser()
        
    def test_parse_date_query(self):
        """Test parsing queries with dates"""
        query = "What did I do on October 5, 2023?"
        params = self.parser.parse_query(query)
        
        self.assertEqual(params.query_type, "recall")
        self.assertIn("October 5, 2023", params.date_filters)
        
    def test_parse_count_query(self):
        """Test parsing count queries"""
        query = "How many times did I mention vacation last month?"
        params = self.parser.parse_query(query)

        self.assertEqual(params.query_type, "count")
        self.assertTrue(params.count_request)
        self.assertIn("vacation", params.keywords)
        self.assertEqual(params.time_range, "last month")

    def test_parse_insight_query(self):
        """Test parsing insight queries"""
        query = "Find insights about my productivity habits from June."
        params = self.parser.parse_query(query)
        
        self.assertEqual(params.query_type, "insight")
        self.assertIn("productivity", params.keywords)
        self.assertIn("habits", params.keywords)
        self.assertIn("June", params.date_filters)

class TestDateUtils(unittest.TestCase):
    def test_parse_natural_date(self):
        """Test parsing natural language dates"""
        # Test specific date
        start, end, is_range = parse_natural_date("October 5, 2023")
        self.assertEqual(start.year, 2023)
        self.assertEqual(start.month, 10)
        self.assertEqual(start.day, 5)
        self.assertEqual(start.hour, 0)
        self.assertEqual(end.hour, 23)
        self.assertFalse(is_range)
        
        # Test relative date
        start, end, is_range = parse_natural_date("yesterday")
        yesterday = datetime.now() - timedelta(days=1)
        self.assertEqual(start.day, yesterday.day)
        self.assertEqual(start.month, yesterday.month)
        self.assertEqual(start.year, yesterday.year)
        self.assertTrue(is_range)
        
    def test_format_timestamp(self):
        """Test formatting timestamps"""
        date = datetime(2023, 10, 5, 14, 30)
        
        # With time
        formatted = format_timestamp(date, include_time=True)
        self.assertEqual(formatted, "October 05, 2023 at 02:30 PM")
        
        # Without time
        formatted = format_timestamp(date, include_time=False)
        self.assertEqual(formatted, "October 05, 2023")

if __name__ == "__main__":
    unittest.main()