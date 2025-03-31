#!/usr/bin/env python3
"""
Diane - Personal Memory Assistant
Main application entry point
"""

import os
import argparse
import yaml
import sys
import json
from datetime import datetime
import readline  # For better CLI input handling
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Add local modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for cross-platform colored output
colorama.init()

from src.processing.transcribe import TranscriptionProcessor
from src.processing.metadata_extractor import MetadataExtractor
from src.processing.db_integration import DatabaseIntegrator
from src.database.sql_db import SQLDatabase, TranscriptMetadata
from src.database.vector_db import VectorDatabase
from src.chains.retrieval_chain import RetrievalChain
from src.chains.query_parser import QueryParser
from src.chains.hybrid_search import HybridSearch
from src.utils.text_to_speech import TTSEngine  # Added import for TTS

def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def speak_text(text, config):
    """
    Convert text to speech and play it
    
    Args:
        text: Text to be spoken
        config: Configuration object containing TTS settings
    """
    try:
        # Get TTS engine from config
        tts_config = config.get("tts", {})
        tts_engine = TTSEngine(tts_config)
        
        # Speak the text
        tts_engine.speak(text)
    except Exception as e:
        print(f"\n{Fore.YELLOW}[TTS Error] {str(e)}{Style.RESET_ALL}")

def process_audio(audio_path, config):
    """Process a single audio file"""
    print(f"\n{Fore.CYAN}Processing audio file: {audio_path}{Style.RESET_ALL}")
    
    # Create transcription processor
    transcriber = TranscriptionProcessor(
        model_size=config["transcription"]["model_size"],
        device=config["audio"]["device"],
        compute_type=config["audio"]["compute_type"]
    )
    
    # Transcribe audio
    print(f"{Fore.YELLOW}Transcribing audio... (this may take a moment){Style.RESET_ALL}")
    transcript_data = transcriber.transcribe_file(audio_path)
    
    # Extract metadata
    print(f"{Fore.YELLOW}Extracting metadata...{Style.RESET_ALL}")
    extractor = MetadataExtractor()
    metadata = extractor.extract_metadata(transcript_data["text"])
    
    # Get base filename and create paths
    file_name = os.path.splitext(os.path.basename(audio_path))[0]
    transcript_dir = os.path.join(os.path.dirname(__file__), "data", "transcripts")
    os.makedirs(transcript_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    transcript_path = os.path.join(transcript_dir, f"{file_name}_{timestamp}.txt")
    metadata_path = os.path.join(transcript_dir, f"{file_name}_{timestamp}_metadata.json")
    
    # Save transcript and metadata
    with open(transcript_path, "w") as f:
        f.write(transcript_data["text"])
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Add to databases
    print(f"{Fore.YELLOW}Adding to databases...{Style.RESET_ALL}")
    db_integrator = DatabaseIntegrator(
        sql_db_path=config["database"]["sql_path"],
        vector_db_path=config["database"]["vector_db_path"],
        embedding_model=config["database"]["embedding_model"]
    )
    
    db_integrator.add_transcript(
        text=transcript_data["text"],
        metadata={
            "file_path": transcript_path,
            "timestamp": datetime.now(),
            "keywords": metadata["keywords"],
            "audio_path": audio_path
        }
    )
    
    print(f"\n{Fore.GREEN}✓ Successfully processed {audio_path}{Style.RESET_ALL}")
    print(f"  Transcript saved to: {transcript_path}")
    print(f"  Metadata saved to: {metadata_path}")
    print(f"  Added to database for search queries")
    
    return transcript_path, metadata_path

def query_memory(query_text, config):
    """Query the memory database with natural language"""
    # Connect to databases
    sql_db = SQLDatabase(config["database"]["sql_path"])
    vector_db = VectorDatabase(
        path=config["database"]["vector_db_path"],
        embedding_model=config["database"]["embedding_model"]
    )
    
    # Parse the query
    query_parser = QueryParser()
    query_params = query_parser.parse_query(query_text)
    
    # Set up hybrid search
    hybrid_searcher = HybridSearch(
        sql_db_path=config["database"]["sql_path"],
        vector_store=vector_db.get_store(),
        sql_model=TranscriptMetadata
    )
    
    # Process different query types
    if query_params.query_type == "count":
        # Perform count query
        results = hybrid_searcher.count_query(query_params)
        display_count_results(results)
    else:
        # Perform search and retrieval
        search_results = hybrid_searcher.search(query_params, max_results=5)
        
        if not search_results:
            print(f"\n{Fore.YELLOW}No memories found matching your query.{Style.RESET_ALL}")
            speak_text("No memories found matching your query.", config)  # Pass config here
            return
        
        # Set up retrieval chain for generating answer
        retrieval_chain = RetrievalChain(
            vector_store=vector_db.get_store(),
            temperature=config["llm"]["temperature"]
        )
        
        # Generate response
        response = retrieval_chain.query(query_text)
        
        # Display results
        display_results(response, search_results)
        speak_text(response, config)  # Pass config here

def display_count_results(results):
    """Display results for count queries"""
    if results["type"] == "error":
        print(f"\n{Fore.RED}Error: {results['message']}{Style.RESET_ALL}")
        return
        
    print(f"\n{Fore.GREEN}===== Keyword Frequency Results ====={Style.RESET_ALL}")
    print(f"{Fore.CYAN}Date range: {results['date_range']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total mentions: {results['total_mentions']}{Style.RESET_ALL}")
    
    for keyword, count in results["counts"].items():
        print(f"- '{keyword}': {count} mentions")
        
    if results["matching_dates"]:
        print(f"\n{Fore.CYAN}Found in recordings from these dates:{Style.RESET_ALL}")
        for date in results["matching_dates"][:5]:  # Show first 5 dates
            print(f"- {date}")
        
        if len(results["matching_dates"]) > 5:
            print(f"... and {len(results['matching_dates']) - 5} more dates")

def display_results(response, search_results):
    """Display query results to the user"""
    print(f"\n{Fore.GREEN}===== Memory Assistant Response ====={Style.RESET_ALL}")
    print(response)
    
    print(f"\n{Fore.GREEN}===== Supporting Memories ====={Style.RESET_ALL}")
    for i, result in enumerate(search_results[:3], 1):  # Show top 3 results
        timestamp = result["metadata"].get("timestamp", "Unknown date")
        if isinstance(timestamp, str):
            date_str = timestamp
        else:
            date_str = timestamp.strftime("%B %d, %Y at %I:%M %p")
            
        print(f"\n{Fore.CYAN}{i}. Memory from {date_str}:{Style.RESET_ALL}")
        
        # Print a snippet of the content (first 150 chars)
        content_snippet = result["content"].replace("\n", " ")
        if len(content_snippet) > 150:
            content_snippet = content_snippet[:150] + "..."
        print(f"   {content_snippet}")

def interactive_mode(config):
    """Run the assistant in interactive mode"""
    print(f"\n{Fore.GREEN}=================================================={Style.RESET_ALL}")
    print(f"{Fore.GREEN}  DIANE - Your Personal Memory Assistant  {Style.RESET_ALL}")
    print(f"{Fore.GREEN}=================================================={Style.RESET_ALL}")
    print("Ask me questions about your recorded memories.")
    print("Type 'exit' or 'quit' to end the session.")
    print(f"{Fore.GREEN}=================================================={Style.RESET_ALL}\n")
    
    while True:
        try:
            query = input(f"\n{Fore.GREEN}You:{Style.RESET_ALL} ").strip()
            
            if query.lower() in ["exit", "quit"]:
                print(f"\n{Fore.CYAN}Thank you for using Diane. Goodbye!{Style.RESET_ALL}")
                break
                
            if not query:
                continue
                
            print(f"\n{Fore.YELLOW}Diane is thinking...{Style.RESET_ALL}")
            query_memory(query, config)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Session interrupted. Goodbye!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Diane - Personal Memory Assistant")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process audio command
    process_parser = subparsers.add_parser("process", help="Process audio file")
    process_parser.add_argument("audio_path", help="Path to audio file")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query your memories")
    query_parser.add_argument("query_text", nargs="?", help="Query text")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    if args.command == "process":
        process_audio(args.audio_path, config)
    elif args.command == "query":
        if args.query_text:
            query_memory(args.query_text, config)
        else:
            print(f"{Fore.RED}Error: Please provide a query text{Style.RESET_ALL}")
    elif args.command == "interactive":
        interactive_mode(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()