import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import numpy as np

def _to_tensor(features):
    """Handle both raw tensor and wrapper object returns from CLIP."""
    if isinstance(features, torch.Tensor):
        return features
    # Newer transformers versions may return a wrapper object
    if hasattr(features, 'pooler_output') and features.pooler_output is not None:
        return features.pooler_output
    if hasattr(features, 'last_hidden_state'):
        return features.last_hidden_state[:, 0, :]
    if hasattr(features, 'text_embeds'):
        return features.text_embeds
    if hasattr(features, 'image_embeds'):
        return features.image_embeds
    raise ValueError(f"Unexpected CLIP output type: {type(features)}")

class TransformerService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load a lightweight model
        print(f"Loading CLIP model on {self.device}...")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model.eval()
        print("CLIP model loaded successfully!")

    def get_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Extracts the image embedding using CLIP."""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            raw = self.model.get_image_features(**inputs)
        features = _to_tensor(raw)
        # Normalize embedding
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.cpu().numpy()[0]

    def get_text_embedding(self, text: str) -> np.ndarray:
        """Extracts text embedding for semantic comparisons."""
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            raw = self.model.get_text_features(**inputs)
        features = _to_tensor(raw)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.cpu().numpy()[0]

    def calculate_semantic_relevance(self, image_embedding: np.ndarray, target_texts: list[str]) -> float:
        """Calculates how relevant the image is to the target texts (e.g., 'wildfire', 'flood')."""
        max_sim = 0.0
        for text in target_texts:
            text_emb = self.get_text_embedding(text)
            sim = float(np.dot(image_embedding, text_emb))
            if sim > max_sim:
                max_sim = sim
        # Map roughly from [-1, 1] to [0, 100]
        score = max(0.0, min(100.0, max_sim * 100))
        return score

transformer_service = TransformerService()
