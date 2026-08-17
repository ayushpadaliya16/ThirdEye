# Fake Social Media Profile Detection REST API

A threat-intelligence API endpoint (`POST /api/analyze-profile`) designed for automated fake social media profile analysis and fraud risk scoring.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start the Server
```bash
npm start
```
The server will run on `http://localhost:3000`. You can open `http://localhost:3000` in your web browser to access the interactive Threat Intelligence Dashboard.

### 3. Run Automated Tests
```bash
npm test
```

---

## 📡 REST API Endpoint Specification

### `POST /api/analyze-profile`

#### Request Headers
```http
Content-Type: application/json
```

#### Request Payload
```json
{
  "username": "@example",
  "platform": "instagram"
}
```

#### cURL Example
```bash
curl -X POST http://localhost:3000/api/analyze-profile \
  -H "Content-Type: application/json" \
  -d '{"username": "@example", "platform": "instagram"}'
```

---

## 📊 Mock Response Contract (Threat-Intelligence Dashboard Schema)

```json
{
  "target_username": "@example",
  "fraud_risk_score": 87,
  "metadata": {
    "follower_count": 142,
    "following_count": 3890,
    "follower_ratio": 27.39,
    "account_age_days": 14,
    "profile_pic_exists": false
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
  "report_timestamp": "2026-08-17T20:36:23.174Z#SHA256:C60B34A6147D94FE"
}
```

---

## 🔑 Data Key Breakdown

| Key | Type | Description |
| :--- | :--- | :--- |
| `target_username` | String | The queried handle normalized with `@` prefix. |
| `fraud_risk_score` | Integer (0–100) | Overall computed risk probability score. |
| `metadata.follower_count` | Integer | Total follower count. |
| `metadata.following_count` | Integer | Total accounts followed. |
| `metadata.follower_ratio` | Number | Ratio of following accounts relative to followers. |
| `metadata.account_age_days` | Integer | Age of the target account in days. |
| `metadata.profile_pic_exists` | Boolean | `true` if custom avatar uploaded, `false` if default. |
| `anomalies` | Array[String] | Specific red flag behavioral and metadata anomalies. |
| `nlp_analysis.bio_spam_likelihood` | String (%) | NLP classification score for bio/description spam. |
| `nlp_analysis.suspicious_keywords_found` | Array[String] | High-risk phishing / scam keywords extracted by NLP. |
| `report_timestamp` | String | Cryptographic ISO 8601 timestamp signed with SHA-256 hash digest. |


## Backend AI Engine
See [backend/README.md](backend/README.md) for the Sentinel AI Engine integration guide and API specs.
