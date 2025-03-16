import os
import sys
import shutil
from datetime import datetime
import certifi
from faster_whisper import WhisperModel
from dotenv import load_dotenv
import logging

# Set the environment variable for the entire process
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()  # This tells requests to use the default certificate store

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import project modules
from src.processing.metadata_extractor import process_transcript, extract_metadata
from src.database.sql_db import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"))

# Initialize Faster Whisper model
model = WhisperModel("small", device="cpu", compute_type="int8")  # Use "cuda" if you have a GPU

def transcribe_audio(audio_path):
    """
    Transcribe audio using Faster Whisper
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    logger.info(f"Transcribing: {os.path.basename(audio_path)}")
    segments, _ = model.transcribe(audio_path, beam_size=5)
    transcript = " ".join(segment.text for segment in segments)
    return transcript

def process_audio(audio_path):
    """
    Process a single audio file - transcribe, extract metadata, and save to database
    
    Args:
        audio_path: Path to the audio file
    """
    try:
        filename = os.path.basename(audio_path)
        logger.info(f"Processing: {filename}")
        
        # Transcribe audio
        transcript = transcribe_audio(audio_path)
        
        # Save transcript
        os.makedirs("data/transcripts", exist_ok=True)
        transcript_filename = f"{os.path.splitext(filename)[0]}.txt"
        transcript_path = os.path.join("data", "transcripts", transcript_filename)
        with open(transcript_path, "w") as f:
            f.write(transcript)
        
        # Process metadata
        metadata = extract_metadata(filename, transcript)
        save_path = os.path.join("data", "metadata", f"{os.path.splitext(filename)[0]}_metadata.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save to database
        db = DatabaseManager()
        transcript_id = db.insert_transcript(
            filename=filename,
            recording_date=datetime.fromisoformat(metadata["date"]),
            transcript_text=transcript,
            keywords=metadata["keywords"]
        )
        logger.info(f"Saved to database with ID: {transcript_id}")
        
        # Move processed audio
        os.makedirs("data/processed_audio", exist_ok=True)
        shutil.move(audio_path, os.path.join("data", "processed_audio", filename))
        
        logger.info(f"Successfully processed: {filename}")

    except Exception as e:
        logger.error(f"Failed to process {os.path.basename(audio_path)}: {str(e)}")
        raise

def process_directory(directory_path):
    """
    Process all audio files in a directory
    
    Args:
        directory_path: Path to the directory containing audio files
    """
    supported_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    
    for filename in os.listdir(directory_path):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            audio_path = os.path.join(directory_path, filename)
            try:
                process_audio(audio_path)
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Process specific file
        audio_file = sys.argv[1]
        if os.path.isfile(audio_file):
            process_audio(audio_file)
        elif os.path.isdir(audio_file):
            process_directory(audio_file)
        else:
            logger.error(f"File or directory not found: {audio_file}")
    else:
        # Example usage
        audio_file = os.path.join("data", "raw_audio", "250206_1156.mp3")
        if os.path.exists(audio_file):
            process_audio(audio_file)
        else:
            logger.info(f"Example file not found. Please provide an audio file path.")
            logger.info(f"Usage: python transcribe.py <audio_file_or_directory>")
