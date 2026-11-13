import chromadb
import uuid
import json
from typing import List, Dict, Any
from chromadb.utils import embedding_functions

class MemoryHelper:
    def __init__(self, persist_dir="memory_db", collection_name="pentest_knowledge"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Use default lightweight embedding model (all-MiniLM-L6-v2)
        # This runs on CPU and is very small/fast.
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.ef
        )

    def add_finding(self, text: str, meta: Dict[str, Any] = None):
        """
        Add a finding (summary) to the vector store.
        """
        if not text:
            return
            
        doc_id = str(uuid.uuid4())
        # Clean metadata values to be strings/ints/floats (chroma restriction)
        cleaned_meta = {}
        if meta:
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    cleaned_meta[k] = v
                else:
                    cleaned_meta[k] = str(v)

        self.collection.add(
            documents=[text],
            metadatas=[cleaned_meta],
            ids=[doc_id]
        )
        print(f"[Memory] Stored: {text[:50]}...")

    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Retrieve relevant findings based on semantic query.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        documents = results.get("documents", [[]])[0]
        return documents

    def clear(self):
        """Reset memory."""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.create_collection(self.collection.name)
        except:
            pass
