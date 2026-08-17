document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('profile-form');
  const inputUsername = document.getElementById('input-username');
  const inputPlatform = document.getElementById('input-platform');
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const presetChips = document.querySelectorAll('.chip');
  const btnCopyJson = document.getElementById('btn-copy-json');

  let currentAnalysisData = null;

  // Handle Tab Switching
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
  });

  // Handle Preset Chips
  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      inputUsername.value = chip.dataset.user;
      inputPlatform.value = chip.dataset.platform;
      executeInspection();
    });
  });

  // Handle Form Submit
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    executeInspection();
  });

  // Handle Copy JSON
  btnCopyJson.addEventListener('click', () => {
    if (currentAnalysisData) {
      navigator.clipboard.writeText(JSON.stringify(currentAnalysisData, null, 2));
      const originalText = btnCopyJson.innerHTML;
      btnCopyJson.innerHTML = `✓ Copied!`;
      setTimeout(() => {
        btnCopyJson.innerHTML = originalText;
      }, 2000);
    }
  });

  async function executeInspection() {
    const username = inputUsername.value.trim();
    const platform = inputPlatform.value;

    if (!username) return;

    try {
      const response = await fetch('/api/analyze-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, platform })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      currentAnalysisData = data;
      renderResults(data, platform);
    } catch (err) {
      console.error('Inspection failed:', err);
      alert('API Inspection Error. Ensure backend server is active.');
    }
  }

  function renderResults(data, platform) {
    // Top Bar Info
    document.getElementById('res-target-handle').textContent = data.target_username;
    document.getElementById('res-target-platform').textContent = platform.toUpperCase();
    document.getElementById('res-timestamp').textContent = data.report_timestamp;

    // Fraud Risk Gauge
    const score = data.fraud_risk_score;
    const gaugeValue = document.getElementById('res-risk-score');
    const gaugeRing = document.getElementById('gauge-ring');
    const riskLabel = document.getElementById('res-risk-label');

    gaugeValue.textContent = score;

    if (score >= 70) {
      gaugeRing.style.borderColor = '#ef4444';
      gaugeRing.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.4)';
      gaugeValue.style.color = '#ef4444';
      riskLabel.textContent = 'CRITICAL THREAT';
      riskLabel.className = 'risk-severity-badge high';
    } else if (score >= 40) {
      gaugeRing.style.borderColor = '#f59e0b';
      gaugeRing.style.boxShadow = '0 0 20px rgba(245, 158, 11, 0.4)';
      gaugeValue.style.color = '#f59e0b';
      riskLabel.textContent = 'MODERATE RISK';
      riskLabel.className = 'risk-severity-badge high';
      riskLabel.style.background = 'rgba(245, 158, 11, 0.2)';
      riskLabel.style.color = '#f59e0b';
      riskLabel.style.borderColor = 'rgba(245, 158, 11, 0.4)';
    } else {
      gaugeRing.style.borderColor = '#10b981';
      gaugeRing.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.4)';
      gaugeValue.style.color = '#10b981';
      riskLabel.textContent = 'LOW RISK / AUTHENTIC';
      riskLabel.className = 'risk-severity-badge low';
    }

    // Metadata
    document.getElementById('res-followers').textContent = data.metadata.follower_count.toLocaleString();
    document.getElementById('res-following').textContent = data.metadata.following_count.toLocaleString();
    document.getElementById('res-ratio').textContent = data.metadata.follower_ratio;
    document.getElementById('res-age').textContent = `${data.metadata.account_age_days} Days`;
    
    const avatarStatus = document.getElementById('res-avatar-status');
    if (data.metadata.profile_pic_exists) {
      avatarStatus.textContent = '✓ Verified Avatar Preset';
      avatarStatus.style.color = '#10b981';
    } else {
      avatarStatus.textContent = '⚠️ Default / Missing Avatar';
      avatarStatus.style.color = '#f59e0b';
    }

    // Anomalies List
    const anomaliesContainer = document.getElementById('res-anomalies');
    anomaliesContainer.innerHTML = '';

    if (data.anomalies.length === 0) {
      anomaliesContainer.innerHTML = `<div class="anomaly-item" style="border-color: #10b981; background: rgba(16, 185, 129, 0.08);"><span style="color: #10b981;">✓ No abnormal profile indicators detected.</span></div>`;
    } else {
      data.anomalies.forEach(anomaly => {
        const item = document.createElement('div');
        item.className = 'anomaly-item';
        item.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>${anomaly}</span>
        `;
        anomaliesContainer.appendChild(item);
      });
    }

    // NLP Analysis
    const nlpFill = document.getElementById('res-nlp-fill');
    const nlpPercent = document.getElementById('res-nlp-percent');
    nlpFill.style.width = data.nlp_analysis.bio_spam_likelihood;
    nlpPercent.textContent = data.nlp_analysis.bio_spam_likelihood;

    const keywordsContainer = document.getElementById('res-keywords');
    keywordsContainer.innerHTML = '';
    if (data.nlp_analysis.suspicious_keywords_found.length === 0) {
      keywordsContainer.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted);">None detected</span>`;
    } else {
      data.nlp_analysis.suspicious_keywords_found.forEach(kw => {
        const span = document.createElement('span');
        span.className = 'kw-badge';
        span.textContent = `"${kw}"`;
        keywordsContainer.appendChild(span);
      });
    }

    // JSON tab highlight
    document.getElementById('res-json-code').textContent = JSON.stringify(data, null, 2);
  }

  // Initial trigger for preview
  executeInspection();
});
