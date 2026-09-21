import random
from datetime import datetime, timedelta

# Scene definitions with mission priorities
SCENES = [
    {'name': 'Forest',        'urgency': 12, 'mission_relevance': 40, 'size_range': (200, 400), 'quality': 85},
    {'name': 'Ocean',         'urgency':  5, 'mission_relevance': 20, 'size_range': (100, 300), 'quality': 80},
    {'name': 'Agriculture',   'urgency': 20, 'mission_relevance': 50, 'size_range': (150, 350), 'quality': 88},
    {'name': 'Urban Area',    'urgency': 35, 'mission_relevance': 60, 'size_range': (300, 600), 'quality': 90},
    {'name': 'Construction',  'urgency': 42, 'mission_relevance': 70, 'size_range': (300, 500), 'quality': 87},
    {'name': 'Cloud-covered', 'urgency':  0, 'mission_relevance':  0, 'size_range': (100, 200), 'quality': 30},
    {'name': 'Ship',          'urgency': 55, 'mission_relevance': 65, 'size_range': ( 50, 150), 'quality': 92},
]

_obs_counter = [0]  # mutable counter for sequential IDs

def _next_id(prefix='OBS'):
    _obs_counter[0] += 1
    return f"{prefix}-{_obs_counter[0]:03d}"

def reset_counter():
    _obs_counter[0] = 0

def generate_dummy_observations(count=50):
    observations = []
    base_time = datetime.now() - timedelta(hours=1)

    for i in range(count):
        scene = random.choice(SCENES)
        obs = {
            'id': _next_id('OBS'),
            'timestamp': base_time + timedelta(minutes=i),
            'latitude': random.uniform(-80.0, 80.0),
            'longitude': random.uniform(-170.0, 170.0),
            'scene': scene['name'],
            'original_size_mb': random.uniform(*scene['size_range']),
            'urgency': max(0, min(100, scene['urgency'] + random.uniform(-5, 5))),
            'mission_relevance': max(0, min(100, scene['mission_relevance'] + random.uniform(-5, 5))),
            'data_quality': max(0, min(100, scene['quality'] + random.uniform(-5, 5))),
        }
        observations.append(obs)

    return observations

def next_emergency_id(event_type='EMG'):
    _obs_counter[0] += 1
    return f"{event_type}-{_obs_counter[0]:03d}"
