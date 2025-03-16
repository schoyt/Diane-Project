import os
from typing import List, Dict, Any, Optional
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

class VectorDatabase:
    """
    Manages the ChromaDB vector store for semantic search on transcript content.
    """
    def __init__(self, db_directory: str = "data/database/vector_store"):
        """
        Initialize the vector database with Sentence Transformer embeddings.
        
        Args:
            db_directory: Directory to store the ChromaDB files
        """
        self.db_directory = db_directory
        
        # Ensure directory exists
        os.makedirs(db_directory, exist_ok=True)
        
        # Initialize embeddings
        try:
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            logger.info("Sentence Transformer embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sentence Transformer embeddings: {e}")
            raise
        
        # Initialize ChromaDB
        try:
            self.db = Chroma(
                persist_directory=db_directory,
                embedding=self.embeddings,
                collection_name="transcript_embeddings"
            )
            logger.info(f"ChromaDB initialized at {db_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_transcript(self, 
                      transcript_id: str, 
                      content: str, 
                      metadata: Dict[str, Any]) -> str:
        """
        Add a transcript to the vector database.
        
        Args:
            transcript_id: Unique identifier for the transcript
            content: Full text content of the transcript
            metadata: Additional information about the transcript (date, keywords, etc.)
            
        Returns:
            ID of the added document
        """
        try:
            # Create document
            document = Document(
                page_content=content,
                metadata=metadata
            )
            
            # Add to vector store
            self.db.add_documents(
                documents=[document],
                ids=[transcript_id]
            )
            
            logger.info(f"Added transcript {transcript_id} to vector database")
            return transcript_id
        except Exception as e:
            logger.error(f"Failed to add transcript {transcript_id} to vector database: {e}")
            raise

    def search(self, 
              query: str, 
              filter_metadata: Optional[Dict[str, Any]] = None, 
              k: int = 5) -> List[Document]:
        """
        Search the vector database for relevant transcripts.
        
        Args:
            query: Natural language query
            filter_metadata: Optional filters to apply (e.g., date range)
            k: Number of results to return
            
        Returns:
            List of matching documents with their content and metadata
        """
        try:
            results = self.db.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )
            
            logger.info(f"Executed search for: '{query}', found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise

    def delete_transcript(self, transcript_id: str) -> None:
        """
        Delete a transcript from the vector database.
        
        Args:
            transcript_id: ID of the transcript to delete
        """
        try:
            self.db._collection.delete(ids=[transcript_id])
            logger.info(f"Deleted transcript {transcript_id} from vector database")
        except Exception as e:
            logger.error(f"Failed to delete transcript {transcript_id}: {e}")
            raise

    def get_transcript(self, transcript_id: str) -> Optional[Document]:
        """
        Retrieve a specific transcript by ID.
        
        Args:
            transcript_id: ID of the transcript to retrieve
            
        Returns:
            Document if found, None otherwise
        """
        try:
            results = self.db._collection.get(ids=[transcript_id])
            
            if results and results['documents']:
                content = results['documents'][0]
                metadata = results['metadatas'][0] if results['metadatas'] else {}
                
                document = Document(
                    page_content=content,
                    metadata=metadata
                )
                
                logger.info(f"Retrieved transcript {transcript_id}")
                return document
            else:
                logger.warning(f"Transcript {transcript_id} not found")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve transcript {transcript_id}: {e}")
            raise

def create_vector_db(documents, persist_directory="data/database/vector_store"):
    # Initialize the Sentence Transformer embeddings
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create and persist the ChromaDB instance
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    vectordb.persist()
    return vectordb