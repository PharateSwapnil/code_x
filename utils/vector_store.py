import faiss
import numpy as np
from typing import List, Dict
import pickle

class VectorStore:
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: List[Dict] = []

    def add_documents(self, documents: List[Dict], embeddings: np.ndarray):
        """Add documents and their embeddings to the store"""
        if len(documents) != embeddings.shape[0]:
            raise ValueError("Number of documents must match number of embeddings")

        self.index.add(embeddings)
        self.documents.extend(documents)

    def search(self, query_embedding: np.ndarray, k: int = 3, max_chars: int = 2000):
        """Search for similar documents with content length limit"""
        query_embedding = query_embedding.reshape(1, -1)
        # Get more results initially to filter by content length
        distances, indices = self.index.search(query_embedding, k * 2)

        results = []
        total_chars = 0

        for idx in indices[0]:
            if idx < len(self.documents):
                doc = self.documents[idx]
                content_length = len(doc['content'])
                if total_chars + content_length <= max_chars:
                    results.append(doc)
                    total_chars += content_length
                    if len(results) >= k:
                        break

        return results

    def save(self, path: str):
        """Save vector store to disk"""
        faiss.write_index(self.index, f"{path}.index")
        with open(f"{path}.docs", 'wb') as f:
            pickle.dump(self.documents, f)

    def load(self, path: str):
        """Load vector store from disk"""
        self.index = faiss.read_index(f"{path}.index")
        with open(f"{path}.docs", 'rb') as f:
            self.documents = pickle.load(f)