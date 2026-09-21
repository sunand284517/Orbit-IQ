import math
from typing import Any, Dict, List


SCALE_MB = 10


def optimize_downlink(available_bandwidth_mb: float, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Solve the 0-1 knapsack problem with dynamic programming.

    Sizes are scaled to tenths of a MB to keep the state space compact while
    preserving enough precision for the dashboard simulation.
    """

    candidates = [obs for obs in observations if obs.get("action", "").lower() != "discard"]

    if not candidates:
        return {
            "selected_ids": [],
            "delayed_ids": [],
            "total_value": 0.0,
            "total_size_mb": 0.0,
        }

    capacity = max(0, int(round(available_bandwidth_mb * SCALE_MB)))
    weights = [max(1, int(math.ceil(obs["compressed_size_mb"] * SCALE_MB))) for obs in candidates]
    values = [float(obs["information_value"]) for obs in candidates]

    dp = [0.0] * (capacity + 1)
    keep = [[False] * (capacity + 1) for _ in candidates]

    for index, (weight, value) in enumerate(zip(weights, values)):
        if weight > capacity:
            continue

        for remaining in range(capacity, weight - 1, -1):
            candidate_value = dp[remaining - weight] + value
            if candidate_value > dp[remaining]:
                dp[remaining] = candidate_value
                keep[index][remaining] = True

    selected_ids = []
    remaining = capacity
    for index in range(len(candidates) - 1, -1, -1):
        weight = weights[index]
        if remaining >= weight and keep[index][remaining]:
            selected_ids.append(candidates[index]["id"])
            remaining -= weight

    selected_ids.reverse()
    selected_set = set(selected_ids)
    delayed_ids = [obs["id"] for obs in candidates if obs["id"] not in selected_set]

    total_size = sum(obs["compressed_size_mb"] for obs in candidates if obs["id"] in selected_set)
    total_value = sum(obs["information_value"] for obs in candidates if obs["id"] in selected_set)

    return {
        "selected_ids": selected_ids,
        "delayed_ids": delayed_ids,
        "total_value": round(float(total_value), 2),
        "total_size_mb": round(float(total_size), 2),
    }


def baseline_downlink(available_bandwidth_mb: float, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Naive FIFO baseline: transmit observations in arrival order until bandwidth is exhausted.
    Used for the before/after comparison.
    """
    selected_ids = []
    remaining = available_bandwidth_mb
    total_value = 0.0
    total_size = 0.0

    for obs in observations:
        if obs.get("action", "").lower() == "discard":
            continue
        size = obs["compressed_size_mb"]
        if size <= remaining:
            selected_ids.append(obs["id"])
            remaining -= size
            total_value += obs["information_value"]
            total_size += size

    return {
        "selected_ids": selected_ids,
        "total_value": round(total_value, 2),
        "total_size_mb": round(total_size, 2),
    }
