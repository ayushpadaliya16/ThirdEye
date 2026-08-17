"""
Pydantic schemas for the Fake Social Media Profile Detection System.

ProfileInput     – OSINT JSON payload describing a social media profile.
RiskBreakdown    – Sub-model for the per-engine risk decomposition.
FraudRiskReport  – Strictly-typed output of the AI Anomaly Detection Engine.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------- #
# Input
# ---------------------------------------------------------------------- #
class ProfileInput(BaseModel):
    """Incoming OSINT profile payload accepted by the API."""

    username: str
    followers_count: int
    following_count: int
    created_at: datetime
    bio: str = ""
    posts: list[str] = Field(
        default_factory=list,
        description="Up to 10 recent post texts for NLP analysis.",
    )
    post_count: int = Field(
        default=0,
        description="Total number of posts published by the account.",
    )
    has_avatar: bool = Field(
        default=True,
        description="Whether the account has a custom profile picture.",
    )


# ---------------------------------------------------------------------- #
# Output
# ---------------------------------------------------------------------- #
class RiskBreakdown(BaseModel):
    """Per-engine risk decomposition within a FraudRiskReport."""

    structural_risk: float = Field(
        ..., ge=0, le=100, description="Metadata anomaly score (0–100)."
    )
    nlp_content_risk: float = Field(
        ..., ge=0, le=100, description="LLM-derived content risk score (0–100)."
    )


class FraudRiskReport(BaseModel):
    """Strictly-typed output of the Fraud Detection Engine."""

    username: str
    fraud_risk_score: float = Field(
        ..., ge=0, le=100, description="Unified fraud risk score (0–100)."
    )
    risk_level: str = Field(
        ..., description='One of: "LOW", "MEDIUM", "HIGH", "CRITICAL".'
    )
    breakdown: RiskBreakdown
    detected_anomalies: list[str] = Field(
        default_factory=list,
        description="Human-readable anomaly flags raised by each engine.",
    )
    llm_analysis_summary: str = Field(
        ..., description="Free-text summary produced by the local LLM."
    )
