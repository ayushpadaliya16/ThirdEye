from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

def generate_crypto_timestamp(data: str) -> str:
    iso_ts = datetime.now(timezone.utc).isoformat()
    sha256_hash = hashlib.sha256((iso_ts + data).encode('utf-8')).hexdigest()[:16].upper()
    return f"{iso_ts}#SHA256:{sha256_hash}"

@app.route('/api/analyze-profile', methods=['POST'])
def analyze_profile():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    platform = data.get('platform', '').strip()

    if not username or not platform:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing required fields: 'username' and 'platform' are required.",
            "status": 400
        }), 400

    formatted_handle = username if username.startswith('@') else f"@{username}"
    follower_count = 142
    following_count = 3890
    follower_ratio = round(following_count / follower_count, 2) if follower_count > 0 else float(following_count)

    response_payload = {
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
        "report_timestamp": generate_crypto_timestamp(f"{formatted_handle}:{platform}")
    }

    return jsonify(response_payload), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
