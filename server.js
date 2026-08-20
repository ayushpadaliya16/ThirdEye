const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

/**
 * Helper function to generate a cryptographic ISO 8601 timestamp string
 * Format: ISO8601#SHA256:<hash>
 */
function generateCryptoTimestamp(dataString) {
  const isoTimestamp = new Date().toISOString();
  const sha256 = crypto
    .createHash('sha256')
    .update(isoTimestamp + dataString)
    .digest('hex');
  return `${isoTimestamp}#SHA256:${sha256.substring(0, 16).toUpperCase()}`;
}

/**
 * Profile Analysis Logic Generator
 * Generates tailored threat intelligence mock data based on input username & platform
 */
function generateProfileAnalysis(usernameInput, platformInput) {
  const platform = (platformInput || 'instagram').toLowerCase();
  const username = usernameInput.startsWith('@') ? usernameInput : `@${usernameInput}`;
  const lowerName = username.toLowerCase();

  let riskScore = 87;
  let followerCount = 142;
  let followingCount = 3890;
  let accountAgeDays = 14;
  let profilePicExists = false;
  let bioSpamLikelihood = "87%";
  let suspiciousKeywords = ["crypto giveaway", "dm for promo", "whatsapp investment", "guaranteed returns"];
  let anomalies = [
    "Following ratio exceeds 10:1 (3890 following vs 142 followers)",
    "Bio contains known phishing & financial scam keywords",
    "Account age is less than 30 days (High velocity creation)",
    "Default avatar detected (No custom profile picture set)",
    "Abnormal posting cadence: 45 posts published within 2 hours of registration"
  ];

  // Tailored presets for testing variety
  if (lowerName.includes('safe') || lowerName.includes('verified') || lowerName.includes('legit')) {
    riskScore = 8;
    followerCount = 18450;
    followingCount = 420;
    accountAgeDays = 1420;
    profilePicExists = true;
    bioSpamLikelihood = "2%";
    suspiciousKeywords = [];
    anomalies = [];
  } else if (lowerName.includes('suspicious') || lowerName.includes('impersonator')) {
    riskScore = 94;
    followerCount = 42;
    followingCount = 7410;
    accountAgeDays = 3;
    profilePicExists = false;
    bioSpamLikelihood = "96%";
    suspiciousKeywords = ["official support", "click link in bio", "urgent verification required", "claim free bonus"];
    anomalies = [
      "Severe follower ratio imbalance (>170:1 following to follower ratio)",
      "High match score with official brand handle (@brand_official) suggesting impersonation",
      "Bio contains deceptive phishing link pattern",
      "Zero verified external links or linked identity providers",
      "Account registered 3 days ago from high-risk IP block"
    ];
  } else if (lowerName.includes('bot')) {
    riskScore = 79;
    followerCount = 89;
    followingCount = 1200;
    accountAgeDays = 21;
    profilePicExists = true;
    bioSpamLikelihood = "81%";
    suspiciousKeywords = ["automated trading", "t.me/crypto_signals", "passive income"];
    anomalies = [
      "Follower ratio exceeds 13:1",
      "Automated interaction pattern detected across comment sections",
      "Bio contains Telegram redirect links",
      "Low content entropy score (repetitive template comments)"
    ];
  }

  // Calculate precise follower ratio
  const ratioValue = followerCount > 0 ? (followingCount / followerCount).toFixed(2) : followingCount;
  const followerRatio = parseFloat(ratioValue);

  const reportTimestamp = generateCryptoTimestamp(`${username}:${platform}:${riskScore}`);

  return {
    target_username: username,
    fraud_risk_score: riskScore,
    metadata: {
      follower_count: followerCount,
      following_count: followingCount,
      follower_ratio: followerRatio,
      account_age_days: accountAgeDays,
      profile_pic_exists: profilePicExists
    },
    anomalies: anomalies,
    nlp_analysis: {
      bio_spam_likelihood: bioSpamLikelihood,
      suspicious_keywords_found: suspiciousKeywords
    },
    report_timestamp: reportTimestamp
  };
}

/**
 * POST /api/analyze-profile
 * Main REST Endpoint for Fake Social Media Profile Analysis
 */
app.post('/api/analyze-profile', (req, res) => {
  const { username, platform } = req.body || {};

  // Input Validation
  if (!username || typeof username !== 'string' || !username.trim()) {
    return res.status(400).json({
      error: "Bad Request",
      message: "Field 'username' is required and must be a non-empty string.",
      status: 400,
      timestamp: new Date().toISOString()
    });
  }

  if (!platform || typeof platform !== 'string' || !platform.trim()) {
    return res.status(400).json({
      error: "Bad Request",
      message: "Field 'platform' is required and must be a non-empty string.",
      status: 400,
      timestamp: new Date().toISOString()
    });
  }

  const supportedPlatforms = ['instagram', 'twitter', 'x', 'facebook', 'linkedin', 'tiktok', 'telegram'];
  const normalizedPlatform = platform.trim().toLowerCase();

  // Generate Analysis Response Payload
  const responseData = generateProfileAnalysis(username.trim(), normalizedPlatform);

  // Return formatted JSON response structured for threat-intelligence dashboard
  return res.status(200).json(responseData);
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'Fake Social Media Profile Detection API', version: '1.0.0' });
});

// Start Server
app.listen(PORT, () => {
  console.log(`[API Architect] Fake Profile Detection REST Server running at http://localhost:${PORT}`);
  console.log(`[API Architect] POST endpoint active at http://localhost:${PORT}/api/analyze-profile`);
});
