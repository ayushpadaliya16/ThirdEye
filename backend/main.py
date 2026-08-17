"""
Sentinel – FastAPI Service for Fake Social Media Profile Detection.

Endpoints:
    GET  /health               – Engine + Ollama liveness probe.
    POST /api/v1/analyze       – Analyse a single profile.
    POST /api/v1/analyze/batch – Analyse a batch of profiles concurrently.

The FraudDetectionEngine is initialised once during the lifespan startup
(IsolationForest fitting + Ollama HTTP client) and torn down gracefully
on shutdown.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_engine import FraudDetectionEngine, OLLAMA_BASE_URL, OLLAMA_PRIMARY_MODEL
from models import FraudRiskReport, ProfileInput

logger = logging.getLogger("sentinel.api")

# ---------------------------------------------------------------------- #
# Engine singleton (populated during lifespan)
# ---------------------------------------------------------------------- #
engine: FraudDetectionEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the detection engine."""
    global engine
    logger.info("Starting FraudDetectionEngine…")
    engine = FraudDetectionEngine()
    logger.info("Engine ready – accepting requests.")
    yield
    logger.info("Shutting down FraudDetectionEngine…")
    await engine.close()
    engine = None
    logger.info("Engine shut down cleanly.")


# ---------------------------------------------------------------------- #
# Application
# ---------------------------------------------------------------------- #
app = FastAPI(
    title="Sentinel – Fake Social Media Profile Detection",
    description=(
        "AI-powered anomaly detection engine combining structural metadata "
        "analysis (IsolationForest) with semantic content evaluation via a "
        "local LLM (Ollama) to produce a unified Fraud Risk Score (0–100)."
    ),
    version="2.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------- #
# CORS – allow Dhruv's Next.js frontend (port 3000) and any other origin
# ---------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------- #
# Global exception handler – catch unhandled errors as structured JSON
# ---------------------------------------------------------------------- #
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return a structured 500 response instead of crashing."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": str(exc),
        },
    )


# ---------------------------------------------------------------------- #
# Response models for batch and health endpoints
# ---------------------------------------------------------------------- #
class BatchAnalysisResponse(BaseModel):
    """Response schema for the batch analysis endpoint."""
    total_scanned: int
    critical_count: int
    results: list[FraudRiskReport]


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""
    status: str
    gpu_acceleration: bool
    model: str


# ---------------------------------------------------------------------- #
# Helper – ensure engine is online
# ---------------------------------------------------------------------- #
def _require_engine() -> FraudDetectionEngine:
    """Return the engine or raise 503 if it hasn't initialised yet."""
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Detection engine is not initialised yet. "
                   "The server is still starting up.",
        )
    return engine


# ====================================================================== #
# Endpoints
# ====================================================================== #

# --- GET /health ------------------------------------------------------- #
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Liveness probe.

    1. Checks whether the ``FraudDetectionEngine`` singleton is initialised.
    2. Pings Ollama at ``/api/tags`` to verify the target model is loaded.

    Returns GPU-acceleration status and the active model name.
    """
    _require_engine()

    # Ping Ollama to verify the model is available
    ollama_tags_url = f"{OLLAMA_BASE_URL}/api/tags"
    gpu_acceleration = False
    active_model = OLLAMA_PRIMARY_MODEL

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(ollama_tags_url)
            resp.raise_for_status()
            tags_data = resp.json()

            # Check if qwen2.5 (or the configured primary model) is loaded
            models_list = tags_data.get("models", [])
            model_names = [m.get("name", "") for m in models_list]

            model_found = any(
                active_model in name for name in model_names
            )
            if not model_found:
                logger.warning(
                    "Model '%s' not found in Ollama. Available: %s",
                    active_model,
                    model_names,
                )

            # Ollama running on GPU if we got a successful response
            # (Ollama auto-uses GPU when available)
            gpu_acceleration = True

    except httpx.ConnectError:
        logger.warning("Ollama is not reachable at %s", OLLAMA_BASE_URL)
        raise HTTPException(
            status_code=503,
            detail=f"Ollama server not reachable at {OLLAMA_BASE_URL}. "
                   "Ensure Ollama is running with the target model loaded.",
        )
    except httpx.TimeoutException:
        logger.warning("Ollama health ping timed out.")
        raise HTTPException(
            status_code=503,
            detail="Ollama server timed out on health check.",
        )
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        # Non-fatal: engine can still work (will degrade gracefully)
        gpu_acceleration = False

    return HealthResponse(
        status="ok",
        gpu_acceleration=gpu_acceleration,
        model=active_model,
    )


# --- POST /api/v1/analyze --------------------------------------------- #
@app.post("/api/v1/analyze", response_model=FraudRiskReport)
async def analyze_profile(profile: ProfileInput) -> FraudRiskReport:
    """
    Analyse a single social-media profile and return a ``FraudRiskReport``
    containing the unified risk score, per-engine breakdown, detected
    anomalies, and the LLM analysis summary.
    """
    det = _require_engine()

    try:
        return await det.process_profile(profile)
    except Exception as exc:
        logger.exception(
            "Failed to process profile '%s'", profile.username
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal processing failure for '{profile.username}': {exc}",
        )


# --- POST /api/v1/analyze/batch --------------------------------------- #
@app.post("/api/v1/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(profiles: list[ProfileInput]) -> BatchAnalysisResponse:
    """
    Analyse a batch of profiles concurrently using ``asyncio.gather``.

    Returns aggregate counts alongside the full per-profile results.
    """
    det = _require_engine()

    if not profiles:
        raise HTTPException(
            status_code=422,
            detail="Payload must contain at least one profile.",
        )

    # Cap batch size to prevent resource exhaustion
    MAX_BATCH = 200
    if len(profiles) > MAX_BATCH:
        raise HTTPException(
            status_code=422,
            detail=f"Batch size {len(profiles)} exceeds the maximum "
                   f"of {MAX_BATCH} profiles per request.",
        )

    async def _safe_process(profile: ProfileInput) -> FraudRiskReport:
        """Process a single profile, catching per-item errors."""
        try:
            return await det.process_profile(profile)
        except Exception as exc:
            logger.error(
                "Batch item '%s' failed: %s", profile.username, exc
            )
            # Return a degraded report rather than failing the entire batch
            from models import RiskBreakdown
            return FraudRiskReport(
                username=profile.username,
                fraud_risk_score=0.0,
                risk_level="LOW",
                breakdown=RiskBreakdown(
                    structural_risk=0.0,
                    nlp_content_risk=0.0,
                ),
                detected_anomalies=[
                    f"Processing failed: {type(exc).__name__}: {exc}"
                ],
                llm_analysis_summary="Analysis could not be completed due to an internal error.",
            )

    # Fire all profile analyses concurrently
    results: list[FraudRiskReport] = await asyncio.gather(
        *[_safe_process(p) for p in profiles]
    )

    critical_count = sum(
        1 for r in results if r.risk_level == "CRITICAL"
    )

    return BatchAnalysisResponse(
        total_scanned=len(results),
        critical_count=critical_count,
        results=results,
    )


# ---------------------------------------------------------------------- #
# Server entrypoint
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
