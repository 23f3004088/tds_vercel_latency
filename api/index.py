from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


with open("telemetry.json", "r") as f:
    telemetry_data = json.load(f)
    print(telemetry_data)

class AnalysisRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/api/latency")
def analyze(payload: AnalysisRequest):
    results = {}
    for region in payload.regions:
        region_data = [r for r in telemetry_data if r["region"] == region]
        if not region_data:
            continue
        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        avg_latency = statistics.mean(latencies)
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        fraction = index - lower
        if upper < n:
            p95_latency = sorted_latencies[lower] + fraction * (sorted_latencies[upper] - sorted_latencies[lower])
        else:
            p95_latency = sorted_latencies[lower]
        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > payload.threshold_ms)
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        }
    return {"regions": results}

@app.get("/")
def root():
    return {"message": "Analytics API is running"}


@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    status_code = exc.status_code if hasattr(exc, 'status_code') else 500
    detail = exc.detail if hasattr(exc, 'detail') else str(exc)
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={"Access-Control-Allow-Origin": "*"}
    )
# # For Vercel serverless function
# from mangum import Mangum
# handler = Mangum(app)