import os
import logging
from typing import List, Dict, Any
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

# Initialize ChromaDB (Local Storage)
client = chromadb.PersistentClient(path="./data/vector_db")

# Use a lightweight local embedding function
embedding_function = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="research_vault",
    embedding_function=embedding_function
)

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts all text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Splits text into smaller chunks for vector storage."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def add_document_to_vault(file_path: str, doc_id: str, metadata: Dict[str, Any]):
    """Parses a PDF, chunks it, and adds it to the vector database."""
    try:
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [metadata for _ in range(len(chunks))]
        
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return True
    except Exception as e:
        logger.error(f"Error adding document to vault: {e}")
        return False

def search_vault(query: str, org_id: int, n_results: int = 3) -> List[str]:
    """Searches the research vault for relevant context."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"org_id": org_id}
        )
        # Flatten the results
        documents = []
        for doc_list in results['documents']:
            documents.extend(doc_list)
        return documents
    except Exception as e:
        logger.error(f"Error searching vault: {e}")
        return []
