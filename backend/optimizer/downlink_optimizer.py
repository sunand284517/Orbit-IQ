import pulp
from typing import List, Dict, Any


def optimize_downlink(available_bandwidth_mb: float, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Solves the 0-1 Knapsack (Binary Integer Linear Program) to maximise
    Total Information Value subject to bandwidth and other constraints.

    Decision variable: x_i ∈ {0, 1}
    Objective:  maximise  Σ information_value_i · x_i
    Subject to: Σ compressed_size_mb_i · x_i  ≤  available_bandwidth_mb
    """

    # Only consider non-discarded observations as candidates
    candidates = [obs for obs in observations if obs.get('action', '').lower() not in ('discard',)]

    if not candidates:
        return {
            'selected_ids': [], 'delayed_ids': [],
            'total_value': 0.0, 'total_size_mb': 0.0,
        }

    prob = pulp.LpProblem("OrbitIQ_Downlink_Optimization", pulp.LpMaximize)

    # Sanitize IDs for PuLP variable names (remove hyphens)
    def safe_var(obs_id: str) -> str:
        return obs_id.replace('-', '_')

    x_vars = {
        obs['id']: pulp.LpVariable(f"x_{safe_var(obs['id'])}", cat='Binary')
        for obs in candidates
    }

    # Objective: maximise total information value
    prob += pulp.lpSum(
        obs['information_value'] * x_vars[obs['id']] for obs in candidates
    ), "Total_Information_Value"

    # Constraint: total transmitted size ≤ available downlink
    prob += pulp.lpSum(
        obs['compressed_size_mb'] * x_vars[obs['id']] for obs in candidates
    ) <= available_bandwidth_mb, "Bandwidth_Constraint"

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    selected_ids, delayed_ids = [], []
    for obs in candidates:
        val = pulp.value(x_vars[obs['id']])
        if val is not None and round(val) == 1:
            selected_ids.append(obs['id'])
        else:
            delayed_ids.append(obs['id'])

    total_size = sum(
        obs['compressed_size_mb'] for obs in candidates if obs['id'] in selected_ids
    )
    total_value = pulp.value(prob.objective) or 0.0

    return {
        'selected_ids': selected_ids,
        'delayed_ids':  delayed_ids,
        'total_value':  round(float(total_value), 2),
        'total_size_mb': round(float(total_size), 2),
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
        if obs.get('action', '').lower() == 'discard':
            continue
        size = obs['compressed_size_mb']
        if size <= remaining:
            selected_ids.append(obs['id'])
            remaining -= size
            total_value += obs['information_value']
            total_size += size

    return {
        'selected_ids': selected_ids,
        'total_value':  round(total_value, 2),
        'total_size_mb': round(total_size, 2),
    }
