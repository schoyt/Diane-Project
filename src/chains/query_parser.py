"""
query_parser.py - Parses natural language queries to extract dates, keywords, and query intent
"""

import spacy
import re
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
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
        1. Date filters: Any specific dates mentioned (e.g., "October 5, 2023"). IMPORTANT: Preserve the original capitalization.
        2. Keywords: Important topic words (e.g., "vacation", "meeting", "John")
        3. Time range: Any time periods mentioned (e.g., "last week", "in June")
        4. Count request: Is the user asking for a count or frequency? (true/false)
        5. Query type: 
           - 'count' if the query mentions "how many", "count", "times" or similar counting words
           - 'insight' if the query asks for "patterns", "insights", "trends", "analysis" or similar analytical concepts
           - 'recall' if the query asks about specific memories or events 
           - 'general' for other types of queries
        
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
                if date not in params.date_filters and date.lower() not in [d.lower() for d in params.date_filters]:
                    params.date_filters.append(date)
            
            # Override query type detection with more explicit rule-based checks
            # Count queries
            if re.search(r"how many|count|frequency|times", query_text.lower()):
                params.count_request = True
                params.query_type = "count"
            
            # Insight queries
            elif re.search(r"insight|pattern|trend|analysis", query_text.lower()):
                params.query_type = "insight"
                    
            return params
            
        except Exception as e:
            print(f"Error in LLM parsing: {str(e)}")
            # Fallback to basic parsing if LLM parsing fails
            return self.basic_parse(query_text)
    
    def basic_parse(self, query_text):
        """
        Enhanced basic parsing using regex and spaCy as fallback
        
        Args:
            query_text: User's natural language query
            
        Returns:
            QueryParameters: Structured query parameters
        """
        doc = self.nlp(query_text)
        
        # Extract dates with original capitalization
        date_filters = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        
        # Extract months if not captured by spaCy's entity recognition
        month_pattern = r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b"
        month_matches = re.findall(month_pattern, query_text, re.IGNORECASE)
        for month in month_matches:
            if month not in date_filters and month.lower() not in [d.lower() for d in date_filters]:
                date_filters.append(month)
        
        # Extract years if not captured by spaCy
        year_pattern = r"\b(20\d{2}|19\d{2})\b"
        year_matches = re.findall(year_pattern, query_text)
        for year in year_matches:
            if year not in date_filters:
                date_filters.append(year)
        
        # Enhanced keyword extraction
        # Extract nouns and proper nouns
        basic_keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2]
        
        # Extract important verbs (excluding common ones)
        common_verbs = {"is", "am", "are", "was", "were", "be", "been", "have", "had", "has", "do", "did", "does", "go", "went", "say", "said"}
        verb_keywords = [token.text for token in doc if token.pos_ == "VERB" and token.text.lower() not in common_verbs and len(token.text) > 2]
        
        # Filter out stopwords
        keywords = []
        for word in basic_keywords + verb_keywords:
            token = self.nlp(word)[0]
            if not token.is_stop:
                keywords.append(word)
        
        # Remove duplicates while preserving order
        keywords = list(dict.fromkeys(keywords))
        
        # Enhanced time range detection
        time_range_patterns = [
            (r"last\s+(\w+)", "last"),
            (r"past\s+(\w+)", "past"),
            (r"previous\s+(\w+)", "previous"),
            (r"this\s+(\w+)", "this"),
            (r"next\s+(\w+)", "next"),
            (r"(january|february|march|april|may|june|july|august|september|october|november|december)(\s+\d{4})?", "month"),
            (r"(\d{4})", "year"),
            (r"yesterday", "yesterday"),
            (r"today", "today"),
            (r"tomorrow", "tomorrow")
        ]
        
        time_range = None
        for pattern, range_type in time_range_patterns:
            match = re.search(pattern, query_text.lower())
            if match:
                if range_type in ["last", "past", "previous", "this", "next"]:
                    time_unit = match.group(1)
                    time_range = f"{match.group(0)}"
                else:
                    time_range = match.group(0)
                break
        
        # Enhanced query type detection
        # Check if it's a count query
        count_patterns = [
            r"how many", r"how often", r"count", r"frequency", r"times", 
            r"instances", r"occurrences", r"how frequently"
        ]
        count_request = any(re.search(pattern, query_text.lower()) for pattern in count_patterns)
        
        # Check if it's an insight query
        insight_patterns = [
            r"pattern", r"trend", r"insight", r"analysis", r"analyze", 
            r"summarize", r"understand", r"discover", r"key points"
        ]
        insight_request = any(re.search(pattern, query_text.lower()) for pattern in insight_patterns)
        
        # Determine query type with improved logic
        if count_request:
            query_type = "count"
        elif insight_request:
            query_type = "insight"
        elif date_filters or any(re.search(r"what.+(happen|do|did|occurred|said|talked)", query_text.lower())):
            query_type = "recall"
        else:
            query_type = "general"
        
        return QueryParameters(
            date_filters=date_filters,
            keywords=keywords,
            time_range=time_range,
            count_request=count_request,
            query_type=query_type
        )