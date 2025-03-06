import numpy as np
from langchain_core.embeddings import Embeddings

class EmbeddingModel:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            # Fallback to a simpler embedding method if sentence-transformers is not available
            self.model = None

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text"""
        if self.model is None:
            # Simple fallback using character frequency as embeddings
            return self._simple_embedding(text)
        return self.model.encode(text)

    def embed_texts(self, texts: list) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        if self.model is None:
            return np.array([self._simple_embedding(text) for text in texts])
        return self.model.encode(texts)

    def _simple_embedding(self, text: str) -> np.ndarray:
        """Simple fallback embedding method using character frequency"""
        # Create a simple frequency-based embedding
        chars = set(''.join(c.lower() for c in text if c.isalnum()))
        embedding = np.zeros(768)  # Same dimension as MiniLM
        for i, c in enumerate(chars):
            embedding[hash(c) % 768] = text.lower().count(c) / len(text)
        return embedding / (np.linalg.norm(embedding) + 1e-8)