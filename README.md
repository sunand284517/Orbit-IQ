# OrbitIQ — Mission-Aware Satellite Data Optimization

## Overview
OrbitIQ uses a **Transformer-based semantic understanding layer + constrained optimization** to decide which satellite observations should be transmitted, compressed, delayed, or discarded when communication bandwidth is limited.

The core objective is:
> **Maximize useful mission information delivered per available communication resource.**

## Problem
Satellites generate terabytes of data daily, but downlink bandwidth is strictly limited. Currently, satellites often transmit blindly or use rigid priorities, leading to bandwidth exhaustion and delayed critical data (e.g., emergencies).

## Solution
1. **Transformer Layer (CLIP)**: Extracts semantic embeddings from observations (simulated via text embedding of the scene type for rapid prototyping).
2. **Novelty Detection**: Compares new embeddings against a rolling history using Cosine Similarity to boost the priority of unique events.
3. **Information Value**: Calculates a holistic 0-100 score based on Semantics, Novelty, Urgency, and Mission Relevance.
4. **Optimization (PuLP)**: Solves the 0-1 Knapsack problem using Integer Linear Programming to maximize the Total Information Value transmitted without exceeding the available downlink bandwidth.

## Setup & Run
### Backend
1. `cd backend`
2. `python -m venv venv`
3. `.\venv\Scripts\Activate`
4. `pip install -r requirements.txt`
5. `uvicorn main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
