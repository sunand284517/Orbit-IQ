import numpy as np
from collections import deque

class NoveltyService:
    """
    Computes novelty via cosine similarity against a rolling embedding history.
    
    Novelty = 1 - max_cosine_similarity(current, history)
    
    Since CLIP embeddings are L2-normalised, dot product = cosine similarity.
    """
    def __init__(self, history_size: int = 30):
        self.history_size = history_size
        self.history: deque = deque(maxlen=history_size)

    def calculate_novelty(self, embedding: np.ndarray) -> float:
        """
        Returns a novelty score in [0, 100].
        100 = completely novel (no similar observation seen before).
        0   = identical to a recent observation.
        """
        if len(self.history) == 0:
            # Very first observation — highly novel by definition
            self.history.append(embedding.copy())
            return 90.0

        # Cosine similarity with all stored embeddings (already L2-normalised)
        similarities = np.array([float(np.dot(embedding, h)) for h in self.history])
        max_sim = float(np.max(similarities))

        # Clamp to [0, 1] first (dot product of unit vectors is in [-1,1])
        max_sim = max(0.0, min(1.0, max_sim))

        # Novelty = inverse of similarity, scaled to [0, 100]
        novelty = (1.0 - max_sim) * 100.0

        # Store *after* computing so the observation competes against prior ones
        self.history.append(embedding.copy())
        return round(novelty, 2)

    def peek_novelty(self, embedding: np.ndarray) -> float:
        """Compute novelty without modifying history (for preview/testing)."""
        if len(self.history) == 0:
            return 90.0
        similarities = np.array([float(np.dot(embedding, h)) for h in self.history])
        max_sim = max(0.0, min(1.0, float(np.max(similarities))))
        return round((1.0 - max_sim) * 100.0, 2)

    def clear_history(self):
        self.history.clear()


novelty_service = NoveltyService()
