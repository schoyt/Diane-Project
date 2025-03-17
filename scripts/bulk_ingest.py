# scripts/bulk_ingest.py
import os
import sys
import time
import glob
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

# Import project modules
from src.processing.transcribe import transcribe_audio
from src.processing.metadata_extractor import extract_metadata, save_metadata
from src.database.sql_db import DatabaseManager
from src.database.vector_db import VectorDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs", "bulk_ingest.log"), mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)

# Supported audio formats
SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']

def process_single_file(audio_path, output_dir, db_manager, vector_db, move_files=True, force=False):
    """
    Process a single audio file - transcribe, extract metadata, and save to databases
    
    Args:
        audio_path: Path to the audio file
        output_dir: Directory to save processed files
        db_manager: Database manager instance
        vector_db: Vector database instance
        move_files: Whether to move processed files to processed_audio directory
        force: Whether to reprocess files that already exist in the database
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        filename = os.path.basename(audio_path)
        file_base = os.path.splitext(filename)[0]
        
        # Check if already processed
        if not force:
            existing_records = db_manager.search_transcripts(file_base)
            if existing_records:
                logger.info(f"Skipping {filename} (already processed - use --force to reprocess)")
                return False
        
        # Transcribe audio
        transcript = transcribe_audio(audio_path)
        
        # Save transcript
        transcript_dir = os.path.join(output_dir, "transcripts")
        os.makedirs(transcript_dir, exist_ok=True)
        transcript_path = os.path.join(transcript_dir, f"{file_base}.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        # Extract metadata
        metadata = extract_metadata(filename, transcript)
        metadata_path = save_metadata(transcript_path, metadata)
        
        # Save to SQL database
        transcript_id = db_manager.insert_transcript(
            filename=filename,
            recording_date=metadata["date"],
            transcript_text=transcript,
            keywords=metadata["keywords"]
        )
        
        # Save to vector database
        vector_db.add_transcript(
            transcript_id=str(transcript_id),
            content=transcript,
            metadata={
                "filename": filename,
                "recording_date": metadata["date"],
                "keywords": metadata["keywords"]
            }
        )
        
        # Move processed file to processed_audio directory
        if move_files:
            processed_dir = os.path.join(output_dir, "processed_audio")
            os.makedirs(processed_dir, exist_ok=True)
            processed_path = os.path.join(processed_dir, filename)
            
            # Don't overwrite existing files
            if os.path.exists(processed_path):
                processed_path = os.path.join(processed_dir, f"{file_base}_{int(time.time())}{os.path.splitext(filename)[1]}")
                
            os.replace(audio_path, processed_path)
            logger.info(f"Moved {filename} to {processed_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing {os.path.basename(audio_path)}: {str(e)}")
        return False

def process_directory(input_dir, output_dir=None, workers=4, recursive=False, move_files=True, force=False):
    """
    Process all audio files in a directory
    
    Args:
        input_dir: Directory containing audio files
        output_dir: Directory to save processed files (default: project_root/data)
        workers: Number of worker threads
        recursive: Whether to process subdirectories
        move_files: Whether to move processed files to processed_audio directory
        force: Whether to reprocess files that already exist in the database
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(project_root, "data")
    
    # Initialize databases
    db_manager = DatabaseManager()
    vector_db = VectorDatabase()
    
    # Find all audio files
    pattern = '**/*' if recursive else '*'
    audio_files = []
    for ext in SUPPORTED_FORMATS:
        audio_files.extend(glob.glob(os.path.join(input_dir, pattern + ext), recursive=recursive))
    
    if not audio_files:
        logger.warning(f"No audio files found in {input_dir}")
        return
    
    logger.info(f"Found {len(audio_files)} audio files to process")
    
    # Process files with progress bar
    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                process_single_file, 
                audio_path, 
                output_dir, 
                db_manager, 
                vector_db, 
                move_files,
                force
            ): audio_path for audio_path in audio_files
        }
        
        # Process as they complete with a progress bar
        with tqdm(total=len(audio_files), desc="Processing audio files") as pbar:
            for future in as_completed(future_to_file):
                audio_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        successful += 1
                    else:
                        # File was skipped, not failed
                        pass
                except Exception as e:
                    logger.error(f"Error processing {os.path.basename(audio_path)}: {str(e)}")
                    failed += 1
                finally:
                    pbar.update(1)
    
    logger.info(f"Bulk ingest complete. Processed {successful} files successfully, {failed} failures, {len(audio_files) - successful - failed} skipped.")

def main():
    """Main entry point for the bulk ingest script"""
    parser = argparse.ArgumentParser(description="Bulk ingest audio files into the Diane system")
    parser.add_argument("input_dir", help="Directory containing audio files to process")
    parser.add_argument("--output-dir", help="Directory to save processed files (default: project_root/data)")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads (default: 4)")
    parser.add_argument("--recursive", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("--no-move", action="store_true", help="Don't move processed files")
    parser.add_argument("--force", action="store_true", help="Reprocess files that already exist in the database")
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1
    
    # Process the directory
    process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        workers=args.workers,
        recursive=args.recursive,
        move_files=not args.no_move,
        force=args.force
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())