from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import hashlib
from datetime import datetime, timezone

app = FastAPI(
    title="Fake Social Media Profile Detection REST API",
    description="Threat Intelligence API endpoint for fake social profile detection and risk analysis.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for Request & Response Validation
class ProfileAnalysisRequest(BaseModel):
    username: str = Field(..., example="@example", description="Social media handle/username")
    platform: str = Field(..., example="instagram", description="Target platform (instagram, twitter, etc.)")

class ProfileMetadata(BaseModel):
    follower_count: int
    following_count: int
    follower_ratio: float
    account_age_days: int
    profile_pic_exists: bool

class NLPAnalysis(BaseModel):
    bio_spam_likelihood: str
    suspicious_keywords_found: List[str]

class ProfileAnalysisResponse(BaseModel):
    target_username: str
    fraud_risk_score: int
    metadata: ProfileMetadata
    anomalies: List[str]
    nlp_analysis: NLPAnalysis
    report_timestamp: str

def generate_crypto_timestamp(data: str) -> str:
    iso_ts = datetime.now(timezone.utc).isoformat()
    sha256_hash = hashlib.sha256((iso_ts + data).encode('utf-8')).hexdigest()[:16].upper()
    return f"{iso_ts}#SHA256:{sha256_hash}"

@app.post("/api/analyze-profile", response_model=ProfileAnalysisResponse, status_code=200)
async def analyze_profile(payload: ProfileAnalysisRequest):
    username = payload.username.strip()
    platform = payload.platform.strip().lower()

    if not username or not platform:
        raise HTTPException(status_code=400, detail="Fields 'username' and 'platform' are required.")

    formatted_handle = username if username.startswith('@') else f"@{username}"

    # Calculate mock ratios
    follower_count = 142
    following_count = 3890
    follower_ratio = round(following_count / follower_count, 2) if follower_count > 0 else float(following_count)

    report_ts = generate_crypto_timestamp(f"{formatted_handle}:{platform}")

    return {
        "target_username": formatted_handle,
        "fraud_risk_score": 87,
        "metadata": {
            "follower_count": follower_count,
            "following_count": following_count,
            "follower_ratio": follower_ratio,
            "account_age_days": 14,
            "profile_pic_exists": False
        },
        "anomalies": [
            "Following ratio exceeds 10:1 (3890 following vs 142 followers)",
            "Bio contains known phishing & financial scam keywords",
            "Account age is less than 30 days (High velocity creation)",
            "Default avatar detected (No custom profile picture set)",
            "Abnormal posting cadence: 45 posts published within 2 hours of registration"
        ],
        "nlp_analysis": {
            "bio_spam_likelihood": "87%",
            "suspicious_keywords_found": [
                "crypto giveaway",
                "dm for promo",
                "whatsapp investment",
                "guaranteed returns"
            ]
        },
        "report_timestamp": report_ts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
