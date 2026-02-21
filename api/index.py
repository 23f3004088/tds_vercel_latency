import json
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

data_path = Path(__file__).parent.parent / "q-vercel-latency.json"

with open(data_path) as f:
    telemetry = json.load(f)

@app.post("/")
async def analyze(request: Request):
    body = await request.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]

    results = {}

    for region in regions:
        region_data = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime"] for r in region_data]

        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return results