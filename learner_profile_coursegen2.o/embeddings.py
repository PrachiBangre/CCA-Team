from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

class EmbeddingIndex:
    def __init__(self):
        self.index = None
        self.vectors = []
        self.text_chunks = []

    def add_texts(self, texts):
        embeddings = model.encode(texts)
        if self.index is None:
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(np.array(embeddings))
        self.vectors.extend(embeddings)
        self.text_chunks.extend(texts)

    def search(self, query, k=5):
        query_emb = model.encode([query])
        distances, indices = self.index.search(np.array(query_emb), k)
        return [self.text_chunks[i] for i in indices]
