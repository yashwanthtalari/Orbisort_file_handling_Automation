import os
import chromadb
from chromadb.config import Settings
from utils.logger import get_logger

logger = get_logger()

# We'll store the vector DB locally in the database folder
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromadb")
os.makedirs(DB_DIR, exist_ok=True)

class VectorStore:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=DB_DIR)
            # Create or get a collection for our files
            # By default chromadb uses a fast internal text embedding model (all-MiniLM-L6-v2) 
            self.collection = self.client.get_or_create_collection(name="orbisort_files")
            logger.info("ChromaDB vector store initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.collection = None

    def add_document(self, file_path: str, content: str, metadata: dict = None):
        if not self.collection or not content.strip():
            return
            
        try:
            # We'll use the file path as the ID
            if not metadata:
                metadata = {}
            # Metadata must contain string, int, bool or float type values
            metadata["path"] = file_path
            
            # Chroma handles embedding generation automatically
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[file_path]
            )
            logger.info(f"Added document to vector DB: {file_path}")
        except Exception as e:
            logger.error(f"Error adding document to vector DB: {e}")

    def semantic_search(self, query: str, n_results: int = 5):
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # results format: {'ids': [['...']], 'distances': [[...]], 'metadatas': [[{...}]] }
            if results and results['ids'] and results['ids'][0]:
                return results['ids'][0] # return list of paths
            return []
        except Exception as e:
            logger.error(f"Vector search failed for '{query}': {e}")
            return []

    def remove_document(self, file_path: str):
        if not self.collection:
            return
        try:
            self.collection.delete(ids=[file_path])
        except Exception as e:
            logger.error(f"Failed to delete document from vector DB: {e}")

# Global instance
vector_store = VectorStore()
