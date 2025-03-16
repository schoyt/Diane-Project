import os
import json
from datetime import datetime
import spacy  # For keyword extraction
from typing import Dict, List, Any

# Load spaCy model for keyword extraction
nlp = spacy.load("en_core_web_sm")

def extract_metadata(filename: str, transcript: str) -> Dict[str, Any]:
    """
    Extract metadata from filename and transcript
    
    Args:
        filename: Name of the audio file
        transcript: Text of the transcript
        
    Returns:
        dict: Extracted metadata
    """
    metadata = {}

    # 1. Extract date from filename
    try:
        # Handle different filename formats
        if '_' in filename:
            # Format: YYYY-MM-DD_note.mp3
            date_str = filename.split("_")[0]
            metadata["date"] = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        elif len(filename) >= 6:
            # Format: YYMMDD_HHMM.mp3
            date_str = filename[:6]
            metadata["date"] = datetime.strptime(date_str, "%y%m%d").date().isoformat()
        else:
            metadata["date"] = datetime.now().date().isoformat()
    except (IndexError, ValueError):
        metadata["date"] = datetime.now().date().isoformat()

    # 2. Extract keywords from transcript
    keywords = extract_keywords(transcript)
    metadata["keywords"] = keywords

    return metadata

def extract_keywords(text: str) -> List[str]:
    """
    Extract meaningful keywords from text using spaCy
    
    Args:
        text: Text to analyze
        
    Returns:
        list: List of extracted keywords
    """
    doc = nlp(text)
    
    # Extract nouns, proper nouns, and important verbs
    keywords = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 3:
            keywords.append(token.lemma_.lower())
        elif token.pos_ == "VERB" and not token.is_stop and len(token.text) > 3:
            keywords.append(token.lemma_.lower())
    
    # Get named entities
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "EVENT"]:
            keywords.append(ent.text.lower())
    
    # Remove duplicates and filter stop words
    filtered_keywords = list(set([k for k in keywords if k.lower() not in nlp.Defaults.stop_words]))
    
    return filtered_keywords

def save_metadata(transcript_path: str, metadata: Dict[str, Any]) -> str:
    """
    Save metadata as a JSON file alongside the transcript
    
    Args:
        transcript_path: Path to the transcript file
        metadata: Metadata to save
        
    Returns:
        str: Path to the saved metadata file
    """
    metadata_path = os.path.splitext(transcript_path)[0] + "_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    return metadata_path

def process_transcript(transcript_path: str) -> Dict[str, Any]:
    """
    Process a single transcript file
    
    Args:
        transcript_path: Path to the transcript file
        
    Returns:
        dict: Extracted metadata
    """
    with open(transcript_path, "r") as f:
        transcript = f.read()
    
    # Extract metadata
    filename = os.path.basename(transcript_path)
    metadata = extract_metadata(filename, transcript)
    
    # Save metadata
    save_metadata(transcript_path, metadata)
    print(f"Processed metadata for: {filename}")
    
    return metadata

if __name__ == "__main__":
    # Example usage
    transcript_path = os.path.join("data", "transcripts", "2024-10-05_note.txt")
    process_transcript(transcript_path)