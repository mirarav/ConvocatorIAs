"""
Módulo para generar representaciones vectoriales.
"""

import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Genera embeddings vectoriales para fragmentos de texto."""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def generate(self, chunks: List[str]) -> List[np.ndarray]:
        """Genera embeddings para cada fragmento de texto."""
        try:
            if not chunks:
                return []
            return self.model.encode(chunks, show_progress_bar=False)
        
        except Exception as e:
            print(f"Error generando embeddings: {str(e)}")
            return []