# Sentinel – Fake Social Media Profile Detection System

## 🚀 Project Overview

Sentinel is a production-grade AI Anomaly Detection Engine built for our fast-paced hackathon. It evaluates OSINT (Open Source Intelligence) profiles to accurately detect fake, bot, or malicious social media accounts.

The engine leverages a dual-architecture approach:
1. **Structural Engine (Scikit-Learn IsolationForest):** Analyzes numerical metadata (follower ratios, account age, posting velocity) and finds statistical outliers based on synthetic distribution baselines.
2. **NLP Engine (Ollama `qwen2.5` Local LLM):** Evaluates profile bios and recent posts for spam indicators, toxicity, engagement-farming, and impersonation.

The backend is exposed via a high-performance **FastAPI** service running concurrently.

---

## 🛠️ Local Setup (For the Team)

Follow these steps to spin up the Sentinel engine locally:

1. **Environment Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start the Local LLM:**
   Ensure Ollama is running and has the required model loaded:
   ```bash
   ollama run qwen2.5
   ```

3. **Start the FastAPI Server:**
   Launch the engine. It will initialize the IsolationForest and connect to Ollama.
   ```bash
   python main.py
   ```
   *The API will be available at `http://0.0.0.0:8000`. Auto-generated Swagger docs are available at `http://localhost:8000/docs`.*

---

## 🌐 Frontend & Integration (For Dhruv & Aayush)

The backend is built with your Next.js dashboard in mind. **CORS is fully enabled** for `localhost:3000` and all other origins. 

### `POST /api/v1/analyze`
Use this endpoint to analyze a single profile in real-time.

**Request Payload (`ProfileInput`):**
```json
{
  "username": "xX_free_crypto_Xx",
  "followers_count": 3,
  "following_count": 7200,
  "created_at": "2026-08-16T12:00:00Z",
  "bio": "🚀 CLICK MY LINK for FREE CRYPTO!!",
  "posts": ["Send 0.1 ETH get 1 ETH back GUARANTEED!!!"],
  "post_count": 340,
  "has_avatar": false
}
```

**Response (`FraudRiskReport`):**
```json
{
  "username": "xX_free_crypto_Xx",
  "fraud_risk_score": 99.78,
  "risk_level": "CRITICAL",
  "breakdown": {
    "structural_risk": 99.8,
    "nlp_content_risk": 98.5
  },
  "detected_anomalies": [
    "Extreme follower imbalance: 3 followers vs 7,200 following (ratio 0.0004)",
    "Missing or minimal bio text (<15 characters)",
    "IsolationForest flagged profile as statistical outlier"
  ],
  "llm_analysis_summary": "High likelihood of spam bot promoting cryptocurrency scams."
}
```

### `POST /api/v1/analyze/batch`
Designed specifically for your **PDF Evidence Dossier** generation. This endpoint handles large batches concurrently via `asyncio.gather`.

**Request:** An array of `ProfileInput` JSON objects (Max 200 items).

**Response:**
```json
{
  "total_scanned": 150,
  "critical_count": 12,
  "results": [
    { /* FraudRiskReport 1 */ },
    { /* FraudRiskReport 2 */ }
  ]
}
```

---

## 🕵️ OSINT Backend (For Pratik)

When sending scraped profiles from your Python scrapers to the Sentinel API, your payloads **MUST** conform to the following Pydantic schema strictly.

### Required Fields & Fallbacks
If your scraper cannot find certain data points, use the exact fallback defaults listed below:

- `username` (string, required): e.g., `"alice_dev"`
- `followers_count` (int, required): e.g., `482`
- `following_count` (int, required): e.g., `310`
- `created_at` (ISO 8601 datetime string, required): e.g., `"2022-01-01T00:00:00Z"`
- `bio` (string): Send `""` (empty string) if missing.
- `posts` (list of strings): Up to 10 recent posts. Send `[]` (empty array) if private or no posts.
- `post_count` (int): Total lifetime posts. Send `0` if unknown.
- `has_avatar` (bool): True if they have a custom profile picture, `false` otherwise. Send `true` if unsure to avoid unfairly penalizing accounts.

**Example Python Payload Generation:**
```python
import httpx
from datetime import datetime, timezone

payload = {
    "username": "target_account",
    "followers_count": 1050,
    "following_count": 200,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "bio": "",  # Fallback for empty bio
    "posts": [], # Fallback for no posts scraped
    "post_count": 0,
    "has_avatar": True
}

# Send to Sentinel API
response = httpx.post("http://localhost:8000/api/v1/analyze", json=payload)
print(response.json())
```
