# Weights must sum to 1.0 — they are configurable here
WEIGHTS = {
    'semantic':  0.25,
    'novelty':   0.25,
    'urgency':   0.30,
    'mission':   0.15,
    'quality':   0.05,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"


def calculate_information_value(
    semantic_score: float,
    novelty_score: float,
    urgency: float,
    mission_relevance: float,
    data_quality: float = 80.0,
    weights: dict = None,
) -> float:
    """
    Calculates the Information Value score in [0, 100].

    Components (all already in [0, 100]):
      semantic_score   – Transformer CLIP similarity to mission-relevant concepts
      novelty_score    – Cosine distance from historical embeddings
      urgency          – Mission-assigned urgency of the scene type
      mission_relevance– Scene-level mission priority
      data_quality     – Estimated image usability (cloud cover, sensor noise, etc.)

    Returns a float in [0, 100].
    """
    w = weights or WEIGHTS

    score = (
        w['semantic'] * semantic_score +
        w['novelty']  * novelty_score  +
        w['urgency']  * urgency        +
        w['mission']  * mission_relevance +
        w['quality']  * data_quality
    )
    return round(min(100.0, max(0.0, score)), 2)


def build_explanation(obs_data: dict) -> str:
    """
    Generate a human-readable explanation for the scoring decision.
    """
    iv = obs_data['information_value']
    action = obs_data.get('action', 'Pending')
    novelty = obs_data['novelty_score']
    urgency = obs_data['urgency']
    mission = obs_data['mission_relevance']
    semantic = obs_data['semantic_score']
    quality = obs_data.get('data_quality', 80)

    reasons = []

    if urgency >= 80:
        reasons.append("very high urgency")
    elif urgency >= 50:
        reasons.append("elevated urgency")
    elif urgency <= 10:
        reasons.append("low urgency")

    if novelty >= 70:
        reasons.append("high novelty (rarely seen pattern)")
    elif novelty <= 20:
        reasons.append("low novelty (similar to recent observations)")

    if mission >= 75:
        reasons.append("strong mission relevance")
    elif mission <= 20:
        reasons.append("low mission relevance")

    if semantic >= 70:
        reasons.append("high semantic importance")

    if quality <= 40:
        reasons.append("poor data quality (cloud/sensor noise)")

    reason_str = " + ".join(reasons) if reasons else "moderate across all dimensions"

    if action == 'Transmit':
        return f"Selected for immediate transmission. {reason_str.capitalize()}."
    elif action == 'Delay':
        return f"Delayed — lower priority given bandwidth constraint. {reason_str.capitalize()}."
    elif action in ('Discard', 'DISCARD'):
        return f"Discarded. {reason_str.capitalize()}."
    else:
        return f"Awaiting optimization. {reason_str.capitalize()}."
