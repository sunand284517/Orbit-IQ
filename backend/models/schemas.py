from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ObservationBase(BaseModel):
    id: str
    timestamp: datetime
    latitude: float
    longitude: float
    scene: str
    original_size_mb: float


class ObservationCalculated(ObservationBase):
    semantic_score: float
    novelty_score: float
    urgency: float
    mission_relevance: float
    data_quality: float = 80.0
    information_value: float
    compressed_size_mb: Optional[float] = None
    compression_quality: Optional[str] = None
    transmission_cost: Optional[float] = None
    value_per_mb: Optional[float] = None        # replaces value_per_bit
    action: Optional[str] = 'Pending'
    reason: Optional[str] = ''
    # Weights used for transparency
    weights: Optional[dict] = None


class OptimizationRequest(BaseModel):
    available_downlink_mb: float
    observations: List[ObservationCalculated]


class OptimizationResult(BaseModel):
    selected_ids: List[str]
    delayed_ids: List[str]
    discarded_ids: List[str]
    total_value: float
    total_size_mb: float
    # Baseline comparison
    baseline_value: float
    baseline_size_mb: float
    observations: List[ObservationCalculated]


# Keep old name for compat
OptimizationResponse = OptimizationResult
