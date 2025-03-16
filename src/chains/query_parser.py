"""
query_parser.py - Parses natural language queries to extract dates, keywords, and query intent
"""

import spacy
import re
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional

class QueryParameters(BaseModel):
    """Parameters extracted from a natural language query"""
    date_filters: List[str] = Field(description="List of date filters extracted from the query")
    keywords: List[str] = Field(description="List of keywords or topics extracted from the query")
    time_range: Optional[str] = Field(description="Time range specification (e.g., 'last week', 'June 2023')")
    count_request: bool = Field(description="Whether the query is asking for a count")
    query_type: str = Field(description="Type of query: 'recall', 'count', 'insight', or 'general'")

class QueryParser:
    def __init__(self):
        """Initialize the query parser with NLP models"""
        self.nlp = spacy.load("en_core_web_sm")
        self.setup_llm_parser()
        
    def setup_llm_parser(self):
        """Set up the LLM-based parser using LangChain"""
        # Initialize the LLM
        self.llm = ChatOpenAI(temperature=0)
        
        # Initialize the output parser
        self.output_parser = JsonOutputParser(pydantic_object=QueryParameters)
        
        # Create the prompt template
        template = """
        You are an AI specialized in parsing natural language queries about personal memories.
        Extract key information from the user's query.
        
        User query: {query}
        
        Extract and categorize the following information:
        1. Date filters: Any specific dates mentioned (e.g., "October 5, 2023")
        2. Keywords: Important topic words (e.g., "vacation", "meeting", "John")
        3. Time range: Any time periods mentioned (e.g., "last week", "in June")
        4. Count request: Is the user asking for a count or frequency? (true/false)
        5. Query type: 'recall' (asking about a specific memory), 'count' (asking how many times something happened), 'insight' (asking for patterns or analysis), or 'general' (other types of queries)
        
        Format your response as a valid JSON object.
        """
        
        self.prompt = ChatPromptTemplate.from_template(template)
        
        # Create the chain
        self.chain = self.prompt | self.llm | self.output_parser
    
    def parse_query(self, query_text):
        """
        Parse a natural language query to extract structured parameters
        
        Args:
            query_text: User's natural language query
            
        Returns:
            QueryParameters: Structured query parameters
        """
        try:
            # Use LLM to parse the query
            params = self.chain.invoke({"query": query_text})
            
            # Additional parsing with spaCy for verification
            doc = self.nlp(query_text)
            
            # Extract entities for verification
            spacy_dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            
            # If spaCy finds dates not caught by the LLM, add them
            for date in spacy_dates:
                if date not in params.date_filters:
                    params.date_filters.append(date)
                    
            return params
            
        except Exception as e:
            # Fallback to basic parsing if LLM parsing fails
            return self.basic_parse(query_text)
    
    def basic_parse(self, query_text):
        """
        Basic parsing using regex and spaCy as fallback
        
        Args:
            query_text: User's natural language query
            
        Returns:
            QueryParameters: Structured query parameters
        """
        doc = self.nlp(query_text.lower())
        
        # Extract dates
        date_filters = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        
        # Extract keywords (nouns)
        keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2]
        
        # Simple regex for time ranges
        time_range_patterns = [
            r"last (week|month|year)",
            r"(january|february|march|april|may|june|july|august|september|october|november|december)(\s+\d{4})?",
            r"in\s+\d{4}"
        ]
        
        time_range = None
        for pattern in time_range_patterns:
            match = re.search(pattern, query_text.lower())
            if match:
                time_range = match.group(0)
                break
        
        # Check if it's a count query
        count_words = ["how many", "count", "frequency", "times"]
        count_request = any(word in query_text.lower() for word in count_words)
        
        # Determine query type
        query_type = "general"
        if any(date in query_text.lower() for date in date_filters):
            query_type = "recall"
        elif count_request:
            query_type = "count"
        elif any(word in query_text.lower() for word in ["pattern", "trend", "insight", "analysis"]):
            query_type = "insight"
        
        return QueryParameters(
            date_filters=date_filters,
            keywords=keywords,
            time_range=time_range,
            count_request=count_request,
            query_type=query_type
        )