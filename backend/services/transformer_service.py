import hashlib
import re
from typing import Any

import numpy as np


EMBEDDING_DIM = 64

SCENE_ALIASES = {
    "wildfire": ("wildfire", "fire", "smoke", "thermal", "emergency"),
    "flood": ("flood", "water", "storm", "inundation", "emergency"),
    "construction": ("construction", "building", "development", "site"),
    "ship": ("ship", "vessel", "maritime", "ocean", "port"),
    "urban area": ("urban", "city", "infrastructure", "roads", "buildings"),
    "agriculture": ("agriculture", "crop", "field", "farmland", "vegetation"),
    "forest": ("forest", "trees", "canopy", "vegetation", "wildland"),
    "ocean": ("ocean", "sea", "water", "marine", "coast"),
    "cloud-covered scene": ("cloud", "cloud-covered", "overcast", "obscured"),
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _token_vector(token: str) -> np.ndarray:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=EMBEDDING_DIM).digest()
    values = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    return (values - 127.5) / 127.5


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)
    return (vector / norm).astype(np.float32)


class TransformerService:
    """
    Lightweight semantic embedding service for serverless deployment.

    The original prototype used a heavyweight ML runtime. That stack is too large
    for Vercel's 500 MB function limit, so this service provides stable normalized
    embeddings from mission-domain tokens and aliases.
    """

    def __init__(self):
        print("Lightweight semantic embedding service ready.")

    def get_image_embedding(self, image: Any) -> np.ndarray:
        """Return a deterministic embedding for image-like metadata."""
        parts = ["image"]
        for attr in ("mode", "format", "size"):
            value = getattr(image, attr, None)
            if value is not None:
                parts.append(str(value))
        return self.get_text_embedding(" ".join(parts))

    def get_text_embedding(self, text: str) -> np.ndarray:
        """Build a stable, normalized semantic embedding for mission text."""
        lowered = text.lower()
        tokens = _tokenize(lowered)

        for scene, aliases in SCENE_ALIASES.items():
            scene_tokens = _tokenize(scene)
            if scene in lowered or all(token in tokens for token in scene_tokens):
                tokens.extend(aliases)

        if not tokens:
            tokens = ["unknown"]

        vector = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        for token in tokens:
            vector += _token_vector(token)

        return _normalize(vector)

    def calculate_semantic_relevance(self, image_embedding: np.ndarray, target_texts: list[str]) -> float:
        """Calculate relevance to mission target concepts."""
        max_sim = 0.0
        for text in target_texts:
            text_emb = self.get_text_embedding(text)
            sim = float(np.dot(image_embedding, text_emb))
            if sim > max_sim:
                max_sim = sim

        return round(max(0.0, min(100.0, max_sim * 100.0)), 2)


transformer_service = TransformerService()
