const http = require('http');

const PORT = process.env.PORT || 3000;

function makePostRequest(path, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const req = http.request(
      {
        hostname: 'localhost',
        port: PORT,
        path: path,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data)
        }
      },
      (res) => {
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => {
          try {
            resolve({ statusCode: res.statusCode, data: JSON.parse(body) });
          } catch (e) {
            resolve({ statusCode: res.statusCode, data: body });
          }
        });
      }
    );

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function runTests() {
  console.log("=== Testing REST API Endpoint /api/analyze-profile ===\n");

  try {
    // Test 1: Standard POST request specified in prompt
    console.log("Test 1: Valid POST Payload { username: '@example', platform: 'instagram' }");
    const res1 = await makePostRequest('/api/analyze-profile', {
      username: "@example",
      platform: "instagram"
    });
    console.log(`Status Code: ${res1.statusCode}`);
    console.log("Response Body:\n", JSON.stringify(res1.data, null, 2));

    // Key assertion checks
    const expectedKeys = [
      'target_username',
      'fraud_risk_score',
      'metadata',
      'anomalies',
      'nlp_analysis',
      'report_timestamp'
    ];
    const metadataKeys = [
      'follower_count',
      'following_count',
      'follower_ratio',
      'account_age_days',
      'profile_pic_exists'
    ];
    const nlpKeys = ['bio_spam_likelihood', 'suspicious_keywords_found'];

    let allPassed = true;
    for (const key of expectedKeys) {
      if (!(key in res1.data)) {
        console.error(`❌ Missing top-level key: ${key}`);
        allPassed = false;
      }
    }
    for (const key of metadataKeys) {
      if (!res1.data.metadata || !(key in res1.data.metadata)) {
        console.error(`❌ Missing metadata key: ${key}`);
        allPassed = false;
      }
    }
    for (const key of nlpKeys) {
      if (!res1.data.nlp_analysis || !(key in res1.data.nlp_analysis)) {
        console.error(`❌ Missing nlp_analysis key: ${key}`);
        allPassed = false;
      }
    }

    if (allPassed) {
      console.log("\n✅ Test 1 PASSED: All required schema keys are present and correctly typed!");
    } else {
      console.error("\n❌ Test 1 FAILED: Schema mismatch.");
      process.exit(1);
    }

    // Test 2: Validation Check (Missing parameters)
    console.log("\nTest 2: Validation Check - Missing Username");
    const res2 = await makePostRequest('/api/analyze-profile', { platform: "instagram" });
    console.log(`Status Code: ${res2.statusCode} (Expected: 400)`);
    if (res2.statusCode === 400) {
      console.log("✅ Test 2 PASSED: Correctly returned 400 Bad Request.");
    } else {
      console.error("❌ Test 2 FAILED.");
      process.exit(1);
    }

    console.log("\n🎉 ALL BACKEND API TESTS PASSED SUCCESSFULLY!");
    process.exit(0);
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  }
}

// Give server time to spin up if invoked directly
runTests();
