from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import random

from models.schemas import ObservationCalculated, OptimizationResult
from data.generator import generate_dummy_observations, next_emergency_id
from services.transformer_service import transformer_service
from services.novelty_service import novelty_service
from services.scoring_service import calculate_information_value, build_explanation, WEIGHTS
from services.compression_service import compress_and_evaluate
from optimizer.downlink_optimizer import optimize_downlink, baseline_downlink

app = FastAPI(title="OrbitIQ Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared application state ────────────────────────────────────────────────
observations: List[ObservationCalculated] = []
available_downlink_mb: float = 1000.0   # 1 GB downlink window
last_optimization_result: Optional[dict] = None

# Mission-relevant anchor texts for semantic scoring
TARGET_TEXTS = [
    'wildfire', 'flood', 'construction', 'ship', 'urban area',
    'agriculture', 'forest', 'ocean', 'cloud-covered scene'
]


# ── Core processing pipeline ─────────────────────────────────────────────────

def process_observation(obs_raw: dict) -> ObservationCalculated:
    """
    Full Semantic -> Novelty -> Scoring -> Compression pipeline for one observation.
    """
    scene = obs_raw['scene']

    # 1. Semantic layer: generate a lightweight text embedding for the scene
    embedding = transformer_service.get_text_embedding(scene)

    # 2. Semantic relevance: cosine sim of embedding vs mission-relevant anchor texts
    semantic_score = transformer_service.calculate_semantic_relevance(embedding, TARGET_TEXTS)

    # 3. Novelty: compare against historical embeddings
    novelty_score = novelty_service.calculate_novelty(embedding)

    # 4. Data quality from raw data (or default)
    data_quality = obs_raw.get('data_quality', 80.0)

    # 5. Information Value (weighted sum, explainable)
    info_val = calculate_information_value(
        semantic_score=semantic_score,
        novelty_score=novelty_score,
        urgency=obs_raw['urgency'],
        mission_relevance=obs_raw['mission_relevance'],
        data_quality=data_quality,
        weights=WEIGHTS,
    )

    # 6. Adaptive compression
    comp_size, comp_quality = compress_and_evaluate(obs_raw['original_size_mb'], info_val)

    # 7. Value/MB metric
    value_per_mb = round(info_val / comp_size, 4) if comp_size > 0 else 0.0

    # 8. Initial action/reason
    if info_val < 30:
        action = 'Discard'
    else:
        action = 'Pending'

    obs = ObservationCalculated(
        id=obs_raw['id'],
        timestamp=obs_raw['timestamp'],
        latitude=obs_raw['latitude'],
        longitude=obs_raw['longitude'],
        scene=scene,
        original_size_mb=obs_raw['original_size_mb'],
        semantic_score=round(semantic_score, 2),
        novelty_score=round(novelty_score, 2),
        urgency=round(obs_raw['urgency'], 2),
        mission_relevance=round(obs_raw['mission_relevance'], 2),
        data_quality=round(data_quality, 2),
        information_value=info_val,
        compressed_size_mb=comp_size,
        compression_quality=comp_quality,
        transmission_cost=comp_size,
        value_per_mb=value_per_mb,
        action=action,
        reason='',
        weights=WEIGHTS,
    )
    obs.reason = build_explanation(obs.dict())
    return obs


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    global observations
    raw_list = generate_dummy_observations(50)
    for raw in raw_list:
        observations.append(process_observation(raw))
    print(f"[OrbitIQ] Startup complete - {len(observations)} observations processed.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/observations", response_model=List[ObservationCalculated])
def get_observations():
    return observations


@app.get("/satellite-status")
def get_status():
    total_orig = sum(o.original_size_mb for o in observations)
    total_comp = sum(o.compressed_size_mb for o in observations)
    transmitted = sum(o.compressed_size_mb for o in observations if o.action == 'Transmit')
    mission_value_delivered = sum(o.information_value for o in observations if o.action == 'Transmit')
    return {
        "satellite_id": "ORBIT-IQ-01",
        "data_generated_mb": round(total_orig, 2),
        "storage_used_mb": round(total_comp, 2),
        "available_downlink_mb": available_downlink_mb,
        "transmitted_mb": round(transmitted, 2),
        "energy_available_percent": 85,
        "system_status": "Nominal",
        "observation_count": len(observations),
        "mission_value_delivered": round(mission_value_delivered, 2),
        "value_per_mb": round(mission_value_delivered / transmitted, 4) if transmitted > 0 else 0.0,
    }


@app.post("/optimize", response_model=OptimizationResult)
def run_optimization():
    global observations, last_optimization_result

    obs_dicts = [o.dict() for o in observations]

    # ILP optimization
    result = optimize_downlink(available_downlink_mb, obs_dicts)

    # Baseline (FIFO) for comparison
    base = baseline_downlink(available_downlink_mb, obs_dicts)

    selected_set = set(result['selected_ids'])

    for obs in observations:
        if obs.action == 'Discard':
            pass  # keep discarded
        elif obs.id in selected_set:
            obs.action = 'Transmit'
        else:
            obs.action = 'Delay'
        obs.reason = build_explanation(obs.dict())

    discarded_ids = [o.id for o in observations if o.action == 'Discard']

    last_optimization_result = {
        'selected_ids': result['selected_ids'],
        'delayed_ids': result['delayed_ids'],
        'discarded_ids': discarded_ids,
        'total_value': result['total_value'],
        'total_size_mb': result['total_size_mb'],
        'baseline_value': base['total_value'],
        'baseline_size_mb': base['total_size_mb'],
    }

    return OptimizationResult(
        observations=observations,
        **last_optimization_result,
    )


@app.get("/optimization-result")
def get_optimization_result():
    if last_optimization_result is None:
        return {"message": "No optimization run yet. POST /optimize first."}
    return last_optimization_result


@app.get("/analytics")
def get_analytics():
    action_counts = {"Transmit": 0, "Delay": 0, "Discard": 0, "Pending": 0}
    for o in observations:
        action_counts[o.action] = action_counts.get(o.action, 0) + 1

    total_orig = sum(o.original_size_mb for o in observations)
    total_comp = sum(o.compressed_size_mb for o in observations)

    top_by_value = sorted(observations, key=lambda x: x.information_value, reverse=True)[:15]

    return {
        "action_counts": action_counts,
        "total_original_mb": round(total_orig, 2),
        "total_compressed_mb": round(total_comp, 2),
        "compression_ratio": round(total_comp / total_orig, 3) if total_orig > 0 else 1.0,
        "top_observations": [
            {
                "id": o.id,
                "scene": o.scene,
                "information_value": o.information_value,
                "novelty_score": o.novelty_score,
                "compressed_size_mb": o.compressed_size_mb,
                "value_per_mb": o.value_per_mb,
                "action": o.action,
            }
            for o in top_by_value
        ],
    }


class EventSimRequest(BaseModel):
    event_type: str


@app.post("/simulate-event", response_model=ObservationCalculated)
def simulate_event(req: EventSimRequest):
    global observations

    event_lower = req.event_type.lower()

    if event_lower == 'wildfire':
        scene = 'Wildfire'
        urgency = random.uniform(88, 98)
        mission_relevance = random.uniform(85, 95)
        data_quality = random.uniform(70, 90)
    elif event_lower == 'flood':
        scene = 'Flood'
        urgency = random.uniform(82, 95)
        mission_relevance = random.uniform(80, 92)
        data_quality = random.uniform(65, 85)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown event type: {req.event_type}")

    prefix = 'WLD' if event_lower == 'wildfire' else 'FLD'
    raw = {
        'id': next_emergency_id(prefix),
        'timestamp': datetime.now(),
        'latitude': random.uniform(-80.0, 80.0),
        'longitude': random.uniform(-170.0, 170.0),
        'scene': scene,
        'original_size_mb': random.uniform(350, 650),
        'urgency': urgency,
        'mission_relevance': mission_relevance,
        'data_quality': data_quality,
    }

    calc = process_observation(raw)
    # Insert at front of queue
    observations.insert(0, calc)
    return calc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
