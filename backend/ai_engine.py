"""
AI Anomaly Detection Engine – Fake Social Media Profile Detection System.

Production-grade engine that combines:
  1. Structural Metadata Anomaly Detection (scikit-learn IsolationForest trained
     on a synthetic normal-user distribution).
  2. Semantic Content Analysis via local LLM (Ollama on RTX 5050 dGPU).
  3. Unified Fraud Risk Scoring Pipeline (0–100).

Connects to a local Ollama instance at http://localhost:11434.
Designed for async FastAPI integration or standalone CLI usage.

Usage (CLI):
    python ai_engine.py profile.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
from sklearn.ensemble import IsolationForest

from models import FraudRiskReport, ProfileInput, RiskBreakdown

# ---------------------------------------------------------------------- #
# Logging
# ---------------------------------------------------------------------- #
logger = logging.getLogger("sentinel.ai_engine")

# ---------------------------------------------------------------------- #
# Ollama configuration
# ---------------------------------------------------------------------- #
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_PRIMARY_MODEL = "qwen2.5"
OLLAMA_FALLBACK_MODEL = "llama3.2"
OLLAMA_TIMEOUT = 90.0  # seconds – generous for first-token latency on large prompts


# ====================================================================== #
#  FraudDetectionEngine
# ====================================================================== #
class FraudDetectionEngine:
    """
    Stateful fraud-detection engine.  Instantiate once at application
    startup; call ``process_profile`` for each incoming OSINT payload.

    Weights
    -------
    - Structural metadata anomaly : 55 %
    - LLM semantic content risk   : 45 %
    """

    STRUCTURAL_WEIGHT: float = 0.55
    CONTENT_WEIGHT: float = 0.45

    # Risk-level thresholds (inclusive lower bound) – recalibrated to
    # reduce false-positives on normal users and celebrities.
    _RISK_BANDS: list[tuple[float, str]] = [
        (80.0, "CRITICAL"),
        (60.0, "HIGH"),
        (35.0, "MEDIUM"),
        (0.0, "LOW"),
    ]

    def __init__(
        self,
        ollama_model: str = OLLAMA_PRIMARY_MODEL,
        ollama_fallback: str = OLLAMA_FALLBACK_MODEL,
    ) -> None:
        self._ollama_model = ollama_model
        self._ollama_fallback = ollama_fallback
        self._http_client: httpx.AsyncClient = httpx.AsyncClient(
            timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=15.0),
        )
        self._isolation_forest = self._train_isolation_forest()
        logger.info(
            "FraudDetectionEngine ready  (primary_model=%s, fallback=%s)",
            ollama_model,
            ollama_fallback,
        )

    # ------------------------------------------------------------------ #
    # Logarithmic feature scaling helper
    # ------------------------------------------------------------------ #
    @staticmethod
    def _log_follower_ratio(followers: float, following: float) -> float:
        """Compute log₁₀-scaled follower ratio.

        ``log10(followers + 1) - log10(following + 1)``

        This compresses extreme ranges (0.0001 … 100 000) into a smooth,
        IsolationForest-friendly space where celebrities and normal users
        both land within the training distribution.
        """
        return float(np.log10(followers + 1) - np.log10(following + 1))

    # ------------------------------------------------------------------ #
    # Sigmoid-based score normalisation
    # ------------------------------------------------------------------ #
    @staticmethod
    def _sigmoid_risk(raw_score: float, midpoint: float = 0.0,
                      steepness: float = 8.0) -> float:
        """Smooth conversion from IsolationForest ``score_samples`` to 0–100.

        Uses a logistic (sigmoid) curve centred at *midpoint* so that mild
        statistical outliers map to moderate risk (~40-50) rather than
        spiking straight to 90+.
        """
        # score_samples: higher → more normal, lower → more anomalous
        # We negate so that more-anomalous → higher risk.
        z = -steepness * (raw_score - midpoint)
        sigmoid = 1.0 / (1.0 + np.exp(-z))
        return float(np.clip(sigmoid * 100.0, 0.0, 100.0))

    # ------------------------------------------------------------------ #
    # IsolationForest – trained on 2 000 synthetic samples
    # ------------------------------------------------------------------ #
    @classmethod
    def _train_isolation_forest(cls) -> IsolationForest:
        """Build and fit an IsolationForest on a realistic synthetic dataset.

        Features (4-D) – all using **log-scaled follower ratio**:
          0 – log_follower_ratio   (log₁₀ scaled)
          1 – account_age_days     (30–3 000)
          2 – posting_velocity     (0.01–5.0 posts/day)
          3 – profile_completeness (0.5–1.0)

        Two population segments:
          • 1 700 normal users     (ratio 0.05–50, age 30–3 000)
          • 300 public figures     (ratio up to 100 000, low following)
        """
        rng = np.random.RandomState(42)

        # ---- Segment 1: Normal users (n=1 700) ---- #
        n_normal = 1_700
        # Raw follower ratios 0.05 – 50  (lognormal centred ≈ 1.2)
        normal_followers = rng.lognormal(mean=5.5, sigma=1.2, size=n_normal)  # ~250 median
        normal_following = rng.lognormal(mean=5.2, sigma=1.0, size=n_normal)  # ~180 median
        normal_log_ratios = np.array([
            cls._log_follower_ratio(f, g)
            for f, g in zip(normal_followers, normal_following)
        ])
        normal_ages = rng.uniform(30, 3_000, size=n_normal)
        normal_velocity = np.clip(
            rng.lognormal(mean=-0.50, sigma=0.70, size=n_normal), 0.01, 5.0
        )
        normal_completeness = rng.beta(5.0, 1.5, size=n_normal) * 0.5 + 0.5

        # ---- Segment 2: Public figures (n=300) ---- #
        n_celeb = 300
        celeb_followers = rng.uniform(10_000, 100_000_000, size=n_celeb)
        celeb_following = rng.uniform(0, 2_000, size=n_celeb)
        celeb_log_ratios = np.array([
            cls._log_follower_ratio(f, g)
            for f, g in zip(celeb_followers, celeb_following)
        ])
        celeb_ages = rng.uniform(365, 3_000, size=n_celeb)
        celeb_velocity = np.clip(
            rng.lognormal(mean=0.0, sigma=0.6, size=n_celeb), 0.01, 5.0
        )
        celeb_completeness = rng.beta(8.0, 1.2, size=n_celeb) * 0.3 + 0.7

        # ---- Combine ---- #
        X_train = np.vstack([
            np.column_stack([normal_log_ratios, normal_ages,
                            normal_velocity, normal_completeness]),
            np.column_stack([celeb_log_ratios, celeb_ages,
                            celeb_velocity, celeb_completeness]),
        ])

        total = n_normal + n_celeb
        model = IsolationForest(
            n_estimators=250,
            contamination=0.03,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train)
        logger.info(
            "IsolationForest fitted on %d synthetic samples "
            "(%d normal + %d public figures)",
            total, n_normal, n_celeb,
        )
        return model

    # ------------------------------------------------------------------ #
    # Structural Metadata Anomaly Extraction
    # ------------------------------------------------------------------ #
    def _analyze_structural_metadata(
        self, profile: ProfileInput
    ) -> tuple[float, list[str]]:
        """
        Compute a structural anomaly risk score (0–100) from numerical
        profile metadata and return ``(risk_score, anomalies)``.

        Handles edge cases:
        - ZeroDivisionError when following_count is 0.
        - Private / restricted profiles where posts may be None or hidden.

        Domain heuristics applied **after** IsolationForest scoring:
        - Celebrity / high-authority override  (cap at 20)
        - Normal-user calibration floor        (<25 for complete profiles)
        - Ghost / lurker differentiation       (35–45, INACTIVE_GHOST)
        """
        anomalies: list[str] = []
        followers = profile.followers_count
        following = profile.following_count

        # ---- Feature: log-scaled follower ratio ---- #
        try:
            log_ratio = self._log_follower_ratio(float(followers), float(following))
        except (ValueError, ZeroDivisionError):
            log_ratio = 0.0
            anomalies.append("Error computing log follower ratio – defaulted to 0")

        if followers == 0 and following == 0:
            anomalies.append(
                "Zero followers AND zero following – ghost account"
            )

        # ---- Feature: account age in days ---- #
        created = profile.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
        account_age_days = max(age_seconds / 86_400, 0.01)

        # ---- Feature: posting velocity ---- #
        is_private_profile = (
            profile.posts is None
            or (profile.post_count == 0 and followers > 50)
        )
        effective_post_count = profile.post_count if profile.post_count else 0
        posting_velocity = effective_post_count / max(account_age_days, 1.0)

        if is_private_profile:
            anomalies.append(
                "Private / restricted profile detected – post data unavailable; "
                "posting velocity may be under-reported"
            )
            posting_velocity = 0.5  # neutral median

        # ---- Feature: profile completeness (0.0–1.0) ---- #
        bio_text = (profile.bio or "").strip()
        has_meaningful_bio = len(bio_text) > 15
        bio_length_norm = min(len(bio_text) / 150.0, 1.0)
        avatar_score = 1.0 if profile.has_avatar else 0.0
        bio_presence_score = 1.0 if has_meaningful_bio else 0.0
        profile_completeness = (
            avatar_score + bio_presence_score + bio_length_norm
        ) / 3.0

        # ---- Human-readable anomaly flags ---- #
        raw_ratio = followers / max(following, 1)

        # Only flag extreme imbalance for LOW-follower accounts (bots),
        # NOT for celebrities who naturally have high ratios.
        is_celebrity = followers > 10_000 and following < 2_000

        if raw_ratio < 0.01 and following > 500:
            anomalies.append(
                f"Extreme follower imbalance: {followers:,} followers "
                f"vs {following:,} following (ratio {raw_ratio:.4f})"
            )
        if raw_ratio > 100 and not is_celebrity:
            anomalies.append(
                f"Suspiciously inflated follower ratio ({raw_ratio:.1f}×) – "
                "possible purchased followers"
            )
        if account_age_days < 3:
            anomalies.append(
                f"Brand-new account: only {account_age_days:.1f} days old"
            )
        elif account_age_days < 7:
            anomalies.append(
                f"Very young account: {account_age_days:.1f} days old"
            )
        if posting_velocity > 20:
            anomalies.append(
                f"Abnormal posting velocity: {posting_velocity:.1f} posts/day"
            )
        if not profile.has_avatar:
            anomalies.append("No custom avatar – using default profile image")
        if not has_meaningful_bio:
            anomalies.append("Missing or minimal bio text (<15 characters)")

        # ---- IsolationForest scoring (log-scaled features) ---- #
        features = np.array(
            [[log_ratio, account_age_days, posting_velocity, profile_completeness]]
        )
        raw_iso_score = self._isolation_forest.score_samples(features)[0]

        # Smooth sigmoid conversion instead of hard linear mapping.
        # midpoint=0.0 centres the sigmoid on the contamination threshold;
        # steepness=8.0 gives a gradual slope so mild outliers ≈ 40-50.
        structural_risk = self._sigmoid_risk(
            raw_iso_score, midpoint=0.0, steepness=8.0
        )

        if structural_risk >= 70:
            anomalies.append(
                f"IsolationForest flagged profile as statistical outlier "
                f"(anomaly score {raw_iso_score:.4f})"
            )

        # ============================================================== #
        # Domain heuristic overrides  (applied AFTER IsolationForest)     #
        # ============================================================== #

        # --- 1. Ghost / Lurker differentiation --- #
        is_ghost = (
            followers == 0
            and following == 0
            and effective_post_count == 0
        )
        if is_ghost:
            # Inactive ghost accounts are LOW / MEDIUM risk (35–45),
            # distinctly below malicious-bot territory (>80).
            structural_risk = float(np.clip(structural_risk, 35.0, 45.0))
            anomalies.append("INACTIVE_GHOST_ACCOUNT – no activity detected")
            logger.debug(
                "Ghost override applied: structural_risk capped to %.1f",
                structural_risk,
            )

        # --- 2. Celebrity / high-authority override --- #
        elif is_celebrity:
            # High-follower, low-following accounts are legitimate public
            # figures.  Cap structural risk at 20.0 unless bio / posting
            # velocity is independently alarming.
            if posting_velocity <= 20:
                structural_risk = min(structural_risk, 20.0)
                anomalies.append(
                    f"Celebrity / high-authority profile detected "
                    f"({followers:,} followers) – structural risk capped at 20"
                )
                logger.debug(
                    "Celebrity override applied: structural_risk=%.1f",
                    structural_risk,
                )

        # --- 3. Normal-user calibration floor --- #
        else:
            is_well_formed = (
                profile.has_avatar
                and has_meaningful_bio
                and account_age_days > 90
                and 0.1 <= raw_ratio <= 10.0
            )
            if is_well_formed and structural_risk >= 25.0:
                structural_risk = min(structural_risk, 24.0)
                anomalies.append(
                    "Well-formed profile – structural risk capped at 25"
                )
                logger.debug(
                    "Normal-user floor applied: structural_risk=%.1f",
                    structural_risk,
                )

        return round(structural_risk, 2), anomalies

    # ------------------------------------------------------------------ #
    # LLM Semantic Content Analysis  (Ollama)
    # ------------------------------------------------------------------ #
    async def _analyze_text_with_local_llm(
        self, bio: str, posts: list[str]
    ) -> tuple[float, str, list[str]]:
        """
        Send bio + recent posts to the local Ollama LLM for semantic fraud
        analysis.  Returns ``(content_risk_score, summary, flagged_reasons)``.

        Gracefully degrades to a neutral score (50) if the LLM is
        unreachable, times out, or returns unparseable output.
        """
        bio_text = (bio or "").strip()
        posts_trimmed = [p[:256] for p in (posts or [])[:10]]

        if not bio_text and not posts_trimmed:
            return 50.0, "No textual content available for semantic analysis.", [
                "Empty bio and no posts – content analysis skipped"
            ]

        # ---- Build the content block ---- #
        content_parts: list[str] = []
        if bio_text:
            content_parts.append(f'Profile Bio: "{bio_text[:512]}"')
        if posts_trimmed:
            formatted = "\n".join(f'  - "{p}"' for p in posts_trimmed)
            content_parts.append(f"Recent Posts:\n{formatted}")
        content_block = "\n\n".join(content_parts)

        prompt = (
            "STRICT INSTRUCTION: Respond ONLY with a valid JSON object. "
            "Do not include markdown formatting, code fences, conversational "
            "text, or any content outside the JSON object.\n\n"
            "You are a social-media fraud-detection AI. Analyze the following "
            "profile content for signs of bot behaviour, spam, impersonation, "
            "or malicious intent.\n\n"
            f"{content_block}\n\n"
            "Your response MUST be a single JSON object with exactly these keys:\n"
            '{\n'
            '  "content_risk_score": <integer from 0 to 100>,\n'
            '  "flagged_reasons": ["string reason 1", "string reason 2"],\n'
            '  "analysis_summary": "Brief 1-2 sentence explanation"\n'
            '}\n\n'
            "Rules:\n"
            "- 'content_risk_score' MUST be an integer between 0 and 100.\n"
            "- 'flagged_reasons' MUST be a JSON array of strings (empty [] if none).\n"
            "- 'analysis_summary' MUST be a single string.\n"
            "- Do NOT wrap the JSON in markdown code fences or backticks.\n\n"
            "Scoring guide:\n"
            "  0-20  : Clearly genuine, natural human content.\n"
            "  21-40 : Mostly normal with minor suspicious elements.\n"
            "  41-60 : Moderate risk – some bot-like or spam patterns.\n"
            "  61-80 : High risk – clear spam / bot / impersonation.\n"
            "  81-100: Critical – obvious scam, spam, or impersonation.\n\n"
            "Indicators to evaluate: spam keywords (crypto, giveaway, free "
            "money, guaranteed returns), excessive CAPS / punctuation, "
            "repetitive phrasing, celebrity or brand impersonation, "
            "suspicious URLs or call-to-action bait, unnatural language "
            "patterns, and engagement-farming tactics."
        )

        # Try primary model, then fallback
        models_to_try = [self._ollama_model, self._ollama_fallback]
        last_error: Exception | None = None

        for model_name in models_to_try:
            try:
                return await self._query_ollama(model_name, prompt)
            except httpx.ConnectError as exc:
                logger.error(
                    "Cannot connect to Ollama at %s – is the server running?",
                    OLLAMA_BASE_URL,
                )
                last_error = exc
                break  # Connection error won't resolve by switching models
            except httpx.TimeoutException as exc:
                logger.warning(
                    "Ollama timed out with model '%s' (%.0fs limit)",
                    model_name,
                    OLLAMA_TIMEOUT,
                )
                last_error = exc
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning(
                    "Failed to parse LLM response from model '%s': %s",
                    model_name,
                    exc,
                )
                last_error = exc
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Ollama HTTP error with model '%s': %s",
                    model_name,
                    exc.response.status_code,
                )
                last_error = exc

        # All attempts failed – graceful degradation
        error_msg = f"{type(last_error).__name__}: {last_error}" if last_error else "Unknown"
        return (
            50.0,
            f"LLM analysis unavailable ({error_msg}). "
            "Content risk defaulted to neutral (50).",
            [f"LLM analysis failed – {error_msg}"],
        )

    async def _query_ollama(
        self, model: str, prompt: str
    ) -> tuple[float, str, list[str]]:
        """
        Execute a single Ollama generate call and parse the JSON response.

        If the LLM returns malformed JSON on the first attempt, automatically
        retries once with a lower temperature (0.05) before raising so the
        caller can fall back to the next model.
        """
        max_attempts = 2
        temperatures = [0.1, 0.05]  # tighter on retry

        for attempt in range(max_attempts):
            temp = temperatures[min(attempt, len(temperatures) - 1)]

            response = await self._http_client.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": temp,
                        "num_predict": 512,
                    },
                },
            )
            response.raise_for_status()

            raw_text = response.json().get("response", "").strip()

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as parse_err:
                if attempt < max_attempts - 1:
                    logger.warning(
                        "LLM (%s) returned malformed JSON (attempt %d/%d, "
                        "temp=%.2f). Retrying with lower temperature…",
                        model,
                        attempt + 1,
                        max_attempts,
                        temp,
                    )
                    continue  # retry
                # Final attempt failed – propagate so caller tries fallback model
                raise parse_err

            # ---- Validate & extract fields ---- #
            if "content_risk_score" not in parsed:
                if attempt < max_attempts - 1:
                    logger.warning(
                        "LLM (%s) JSON missing 'content_risk_score' key "
                        "(attempt %d/%d). Retrying…",
                        model,
                        attempt + 1,
                        max_attempts,
                    )
                    continue
                raise KeyError("content_risk_score")

            content_risk = float(np.clip(parsed["content_risk_score"], 0, 100))
            flagged_reasons = parsed.get("flagged_reasons", [])
            summary = parsed.get("analysis_summary", "LLM analysis completed.")

            if not isinstance(flagged_reasons, list):
                flagged_reasons = [str(flagged_reasons)]
            flagged_reasons = [str(r) for r in flagged_reasons]

            logger.info(
                "LLM (%s) content_risk=%.1f  reasons=%d  (attempt %d, temp=%.2f)",
                model,
                content_risk,
                len(flagged_reasons),
                attempt + 1,
                temp,
            )
            return content_risk, summary, flagged_reasons

        # Should not reach here, but satisfy type checker
        raise RuntimeError(f"_query_ollama: exhausted {max_attempts} attempts")

    # ------------------------------------------------------------------ #
    # Risk-level classification
    # ------------------------------------------------------------------ #
    @classmethod
    def _classify_risk_level(cls, score: float) -> str:
        """Map a 0–100 unified score to LOW / MEDIUM / HIGH / CRITICAL."""
        for threshold, label in cls._RISK_BANDS:
            if score >= threshold:
                return label
        return "LOW"

    # ------------------------------------------------------------------ #
    # Main pipeline
    # ------------------------------------------------------------------ #
    async def process_profile(self, profile: ProfileInput) -> FraudRiskReport:
        """
        Primary entry point.  Runs structural + LLM analysis and returns a
        unified ``FraudRiskReport``.
        """
        # Structural analysis (CPU-bound, fast – run synchronously)
        structural_risk, structural_anomalies = self._analyze_structural_metadata(
            profile
        )

        # LLM content analysis (I/O-bound – awaited)
        content_risk, llm_summary, content_anomalies = (
            await self._analyze_text_with_local_llm(profile.bio, profile.posts)
        )

        # ---- Unified weighted score ---- #
        unified_score = round(
            self.STRUCTURAL_WEIGHT * structural_risk
            + self.CONTENT_WEIGHT * content_risk,
            2,
        )
        unified_score = float(np.clip(unified_score, 0.0, 100.0))

        # ---- Assemble report ---- #
        all_anomalies = structural_anomalies + content_anomalies
        risk_level = self._classify_risk_level(unified_score)

        return FraudRiskReport(
            username=profile.username,
            fraud_risk_score=unified_score,
            risk_level=risk_level,
            breakdown=RiskBreakdown(
                structural_risk=round(structural_risk, 2),
                nlp_content_risk=round(content_risk, 2),
            ),
            detected_anomalies=all_anomalies,
            llm_analysis_summary=llm_summary,
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def close(self) -> None:
        """Release the underlying HTTP client."""
        await self._http_client.aclose()
        logger.info("FraudDetectionEngine shut down.")


# ====================================================================== #
# Standalone CLI entry point
# ====================================================================== #
async def _run_cli(input_path: str) -> None:
    """Read a JSON profile from *input_path*, analyse it, and print the report."""
    path = Path(input_path)
    if not path.exists():
        print(f"Error: file not found – {path}", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(path.read_text(encoding="utf-8"))
    profile = ProfileInput(**raw)

    engine = FraudDetectionEngine()
    try:
        report = await engine.process_profile(profile)
        print(json.dumps(report.model_dump(), indent=2, default=str))
    finally:
        await engine.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_engine.py <profile.json>", file=sys.stderr)
        print(
            "\nReads an OSINT JSON payload matching the ProfileInput schema,",
            file=sys.stderr,
        )
        print(
            "runs the full detection pipeline, and prints the FraudRiskReport.",
            file=sys.stderr,
        )
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    asyncio.run(_run_cli(sys.argv[1]))
