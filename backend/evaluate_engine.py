"""
Sentinel Benchmark Suite – evaluate_engine.py

Runs the FraudDetectionEngine against five distinct edge-case profiles
and prints a clean summary table to the console.

Profiles tested:
  a) Clear bot         – high following, near-zero followers, spam bio
  b) Normal active user – balanced metrics, genuine bio
  c) Lurker            – zero everything, no avatar, blank bio
  d) Verified celebrity – millions of followers, 0 following
  e) Empty payload     – missing / minimal keys (tests Pydantic defaults)

Usage:
    # Ensure Ollama is running and the model is loaded
    python evaluate_engine.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone

from ai_engine import FraudDetectionEngine
from models import ProfileInput

# ---------------------------------------------------------------------- #
# Edge-case profiles
# ---------------------------------------------------------------------- #
NOW = datetime.now(timezone.utc)

EDGE_CASES: list[dict] = [
    {
        "label": "🤖 Clear Bot",
        "profile": {
            "username": "xX_free_crypto_Xx_99",
            "followers_count": 3,
            "following_count": 7200,
            "created_at": (NOW - timedelta(hours=18)).isoformat(),
            "bio": "🚀 CLICK MY LINK for FREE CRYPTO!! Guaranteed returns 💰💰 "
                   "DM for giveaway!! WIN BIG NOW!!!",
            "posts": [
                "Send 0.1 ETH get 1 ETH back GUARANTEED!!!",
                "FREE MONEY method exposed!! Click link in bio 💵💵",
            ],
            "post_count": 340,
            "has_avatar": False,
        },
    },
    {
        "label": "✅ Normal Active User",
        "profile": {
            "username": "alice_dev",
            "followers_count": 482,
            "following_count": 310,
            "created_at": (NOW - timedelta(days=3 * 365)).isoformat(),
            "bio": "Software engineer @ Acme Corp. I write about distributed "
                   "systems and bake sourdough on weekends.",
            "posts": [
                "Just shipped v2.4 – excited about the new caching layer!",
                "Beautiful sunrise hike this morning 🌄",
            ],
            "post_count": 215,
            "has_avatar": True,
        },
    },
    {
        "label": "👻 Lurker (Ghost Account)",
        "profile": {
            "username": "empty_shell_000",
            "followers_count": 0,
            "following_count": 0,
            "created_at": (NOW - timedelta(days=400)).isoformat(),
            "bio": "",
            "posts": [],
            "post_count": 0,
            "has_avatar": False,
        },
    },
    {
        "label": "⭐ Verified Celebrity",
        "profile": {
            "username": "elonmusk_official",
            "followers_count": 12_500_000,
            "following_count": 0,
            "created_at": (NOW - timedelta(days=6 * 365)).isoformat(),
            "bio": "CEO of SpaceCorp. Making life multiplanetary. 🚀",
            "posts": [
                "Rocket launch scheduled for Friday. Stay tuned.",
                "Working on next-gen neural interfaces.",
            ],
            "post_count": 4800,
            "has_avatar": True,
        },
    },
    {
        "label": "❓ Empty Payload (Missing Keys)",
        "profile": {
            "username": "unknown",
            "followers_count": 0,
            "following_count": 0,
            "created_at": NOW.isoformat(),
        },
        # Relies on Pydantic defaults: bio="", posts=[], post_count=0,
        # has_avatar=True
    },
]

# ---------------------------------------------------------------------- #
# Table rendering
# ---------------------------------------------------------------------- #
SEPARATOR = "═" * 96
THIN_SEP = "─" * 96


def print_table(rows: list[dict]) -> None:
    """Print a formatted console table from a list of result dicts."""
    header = (
        f"{'#':<3} {'Label':<28} {'Username':<24} "
        f"{'Struct':>7} {'NLP':>7} {'Final':>7}  {'Level':<10}"
    )
    print(f"\n{SEPARATOR}")
    print("  SENTINEL BENCHMARK RESULTS")
    print(SEPARATOR)
    print(header)
    print(THIN_SEP)

    for i, r in enumerate(rows, 1):
        level = r["risk_level"]
        # Colour hint via emoji
        level_icon = {
            "LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"
        }.get(level, "⚪")

        print(
            f"{i:<3} {r['label']:<28} {r['username']:<24} "
            f"{r['structural']:>7.1f} {r['nlp']:>7.1f} {r['final']:>7.1f}  "
            f"{level_icon} {level:<10}"
        )

    print(SEPARATOR)
    print()


# ---------------------------------------------------------------------- #
# Main benchmark
# ---------------------------------------------------------------------- #
async def run_benchmark() -> None:
    """Instantiate the engine, process all edge cases, and print results."""
    engine = FraudDetectionEngine()

    # Build ProfileInput objects (Pydantic fills missing keys with defaults)
    profiles_with_labels: list[tuple[str, ProfileInput]] = []
    for case in EDGE_CASES:
        label = case["label"]
        try:
            profile = ProfileInput(**case["profile"])
        except Exception as exc:
            print(f"⚠  Skipping '{label}': {exc}")
            continue
        profiles_with_labels.append((label, profile))

    # Run all profiles concurrently via asyncio.gather
    print(f"\n⏳ Processing {len(profiles_with_labels)} edge-case profiles…\n")

    async def _process(label: str, profile: ProfileInput) -> dict:
        report = await engine.process_profile(profile)
        return {
            "label": label,
            "username": report.username,
            "structural": report.breakdown.structural_risk,
            "nlp": report.breakdown.nlp_content_risk,
            "final": report.fraud_risk_score,
            "risk_level": report.risk_level,
            "anomalies": report.detected_anomalies,
            "llm_summary": report.llm_analysis_summary,
        }

    tasks = [_process(label, profile) for label, profile in profiles_with_labels]
    results = await asyncio.gather(*tasks)

    # Print summary table
    print_table(list(results))

    # Print detailed anomalies per profile
    print("DETAILED ANOMALIES")
    print(THIN_SEP)
    for r in results:
        anomalies = r["anomalies"]
        tag = f"{r['label']}  @{r['username']}"
        if anomalies:
            print(f"\n  {tag}")
            for a in anomalies:
                print(f"    ⚠  {a}")
        else:
            print(f"\n  {tag}  —  No anomalies detected ✓")

    print(f"\n{THIN_SEP}")
    print("LLM ANALYSIS SUMMARIES")
    print(THIN_SEP)
    for r in results:
        print(f"\n  {r['label']}  @{r['username']}")
        print(f"    {r['llm_summary']}")

    print(f"\n{SEPARATOR}\n")

    await engine.close()


# ---------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    try:
        asyncio.run(run_benchmark())
    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
        sys.exit(130)
