"""
UC2 — App Store Policy Compliance Agent
Signal sources:
  1. submission-queue     — new app submissions and update diffs
  2. policy-kb            — policy rule lookup events (simulates KB query traffic)
  3. submission-history   — prior review outcomes for the same bundle IDs
  4. escalation-queue     — human-flagged ambiguous cases awaiting AI recommendation

Seeded anomaly: a cluster of apps from the same developer account begins
submitting updates that progressively obscure data collection practices —
starting with incomplete privacy manifests (subtle), escalating to
misclassified data types (moderate), and finally explicit guideline
violations around user tracking without consent disclosure (obvious).
"""
from __future__ import annotations

import random

from techcompany_sim.core.stream import AnomalyIntensity, EventStream, SignalSource, StreamContext
from techcompany_sim.core.cli import make_cli, weighted_choice

# ── Reference data ────────────────────────────────────────────────────────────

APP_CATEGORIES   = ["Games", "Productivity", "Health & Fitness", "Finance",
                    "Social Networking", "Photo & Video", "Education", "Shopping",
                    "Entertainment", "Business", "Utilities"]
PLATFORMS        = ["iOS", "macOS", "watchOS", "tvOS", "visionOS"]
CAPABILITIES     = ["camera", "location-always", "location-when-in-use", "contacts",
                    "microphone", "health-data", "face-id", "push-notifications",
                    "background-fetch", "tracking"]
POLICY_SECTIONS  = ["2.1 App Completeness", "2.3 Accurate Metadata", "3.1.1 In-App Purchase",
                    "4.2 Minimum Functionality", "5.1.1 Data Collection and Storage",
                    "5.1.2 Data Use and Sharing", "5.3.4 VPN Apps",
                    "1.1.6 App Store Reviews", "4.8 Sign in with Techcompany",
                    "2.5.4 Background Processes"]
VIOLATION_LEVELS = ["reject", "warn", "flag-for-review", "approve"]
JURISDICTIONS    = ["US", "EU", "UK", "DE", "JP", "AU", "IN", "BR"]

ANOMALY_DEVELOPER = "dev_account_7741"
ANOMALY_BUNDLE    = "com.obscure.tracker"


def random_bundle_id(rng: random.Random) -> str:
    tld  = rng.choice(["com", "io", "app", "co"])
    name = rng.choice(["nova", "swift", "peak", "arc", "bloom", "flux", "drift", "zest"])
    app  = rng.choice(["pro", "lite", "hub", "sync", "kit", "go", "ai", "plus"])
    return f"{tld}.{name}.{app}"


def random_capabilities(rng: random.Random, n: int = 3) -> list[str]:
    return rng.sample(CAPABILITIES, min(n, len(CAPABILITIES)))


# ── Signal Source 1: Submission Queue ────────────────────────────────────────

def submission_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    caps = random_capabilities(rng, rng.randint(1, 5))
    return {
        "bundle_id":          random_bundle_id(rng),
        "developer_account":  f"dev_account_{rng.randint(1000, 9999)}",
        "app_category":       rng.choice(APP_CATEGORIES),
        "platform":           rng.choice(PLATFORMS),
        "version":            f"{rng.randint(1,5)}.{rng.randint(0,9)}.{rng.randint(0,9)}",
        "declared_capabilities": caps,
        "privacy_manifest_complete": rng.random() > 0.08,
        "data_types_declared": rng.sample(
            ["usage-data", "contact-info", "location", "identifiers", "purchases", "diagnostics"],
            rng.randint(0, 4),
        ),
        "iap_configured":     rng.random() > 0.5,
        "content_rating":     rng.choice(["4+", "9+", "12+", "17+"]),
        "geographic_availability": rng.sample(JURISDICTIONS, rng.randint(3, 8)),
        "submission_type":    rng.choice(["new", "update", "update", "update"]),
        "review_notes":       None,
    }


def submission_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.45:
        # The anomaly developer submitting progressively worse updates
        if intensity == AnomalyIntensity.SUBTLE:
            # Incomplete privacy manifest — easy to miss
            caps = ["location-always", "tracking"]
            return {
                "bundle_id":          ANOMALY_BUNDLE,
                "developer_account":  ANOMALY_DEVELOPER,
                "app_category":       "Social Networking",
                "platform":           "iOS",
                "version":            f"3.{rng.randint(1,9)}.0",
                "declared_capabilities": caps,
                "privacy_manifest_complete": False,
                "data_types_declared": ["usage-data"],   # underdeclared
                "iap_configured":     False,
                "content_rating":     "4+",
                "geographic_availability": JURISDICTIONS,
                "submission_type":    "update",
                "review_notes":       "Minor UI improvements",
            }
        elif intensity == AnomalyIntensity.MODERATE:
            return {
                "bundle_id":          ANOMALY_BUNDLE,
                "developer_account":  ANOMALY_DEVELOPER,
                "app_category":       "Social Networking",
                "platform":           "iOS",
                "version":            f"3.{rng.randint(10,19)}.0",
                "declared_capabilities": ["location-always", "tracking", "contacts", "camera"],
                "privacy_manifest_complete": False,
                "data_types_declared": ["usage-data", "diagnostics"],  # misclassified
                "iap_configured":     False,
                "content_rating":     "4+",
                "geographic_availability": JURISDICTIONS,
                "submission_type":    "update",
                "review_notes":       "Performance optimizations",
            }
        else:  # OBVIOUS
            return {
                "bundle_id":          ANOMALY_BUNDLE,
                "developer_account":  ANOMALY_DEVELOPER,
                "app_category":       "Social Networking",
                "platform":           "iOS",
                "version":            f"4.0.0",
                "declared_capabilities": ["location-always", "tracking", "contacts",
                                          "camera", "microphone"],
                "privacy_manifest_complete": False,
                "data_types_declared": [],   # nothing declared
                "iap_configured":     False,
                "content_rating":     "4+",
                "geographic_availability": JURISDICTIONS,
                "submission_type":    "update",
                "review_notes":       "Bug fixes",
            }

    return submission_normal(ctx)


# ── Signal Source 2: Policy KB Activity ──────────────────────────────────────

def policy_kb_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "query_type":       rng.choice(["rule-lookup", "precedent-search", "jurisdiction-check"]),
        "policy_section":   rng.choice(POLICY_SECTIONS),
        "jurisdiction":     rng.choice(JURISDICTIONS),
        "result_count":     rng.randint(1, 12),
        "confidence":       round(rng.uniform(0.7, 0.99), 2),
        "triggered_by":     random_bundle_id(rng),
    }


def policy_kb_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    if rng.random() < 0.5:
        return {
            "query_type":     "rule-lookup",
            "policy_section": "5.1.1 Data Collection and Storage",
            "jurisdiction":   rng.choice(["EU", "DE", "US"]),
            "result_count":   rng.randint(3, 8),
            "confidence":     round(rng.uniform(0.85, 0.99), 2),
            "triggered_by":   ANOMALY_BUNDLE,
        }
    return policy_kb_normal(ctx)


# ── Signal Source 3: Submission History ──────────────────────────────────────

OUTCOMES = ["approved", "approved", "approved", "rejected", "warned", "revision-requested"]


def history_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    outcome = rng.choice(OUTCOMES)
    return {
        "bundle_id":        random_bundle_id(rng),
        "developer_account":f"dev_account_{rng.randint(1000, 9999)}",
        "review_date":      f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "outcome":          outcome,
        "violation_section":rng.choice(POLICY_SECTIONS) if outcome != "approved" else None,
        "remediation_taken":rng.random() > 0.3 if outcome != "approved" else None,
        "resubmission_count":rng.randint(0, 4),
    }


def history_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    if rng.random() < 0.4:
        return {
            "bundle_id":          ANOMALY_BUNDLE,
            "developer_account":  ANOMALY_DEVELOPER,
            "review_date":        f"2024-{rng.randint(6,11):02d}-{rng.randint(1,28):02d}",
            "outcome":            rng.choice(["warned", "revision-requested", "rejected"]),
            "violation_section":  "5.1.1 Data Collection and Storage",
            "remediation_taken":  False,
            "resubmission_count": rng.randint(3, 8),
        }
    return history_normal(ctx)


# ── Signal Source 4: Escalation Queue ────────────────────────────────────────

ESCALATION_REASONS = [
    "ambiguous capability declaration",
    "borderline content rating",
    "novel business model not covered by guidelines",
    "regional regulatory conflict",
    "prior violation pattern",
    "DMA compliance uncertainty",
]


def escalation_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "bundle_id":          random_bundle_id(rng),
        "escalation_reason":  rng.choice(ESCALATION_REASONS),
        "reviewer_confidence":round(rng.uniform(0.3, 0.65), 2),
        "policy_sections_cited": rng.sample(POLICY_SECTIONS, rng.randint(1, 3)),
        "recommended_disposition": None,   # awaiting AI recommendation
        "urgency":            rng.choice(["low", "medium", "high"]),
    }


def escalation_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    if rng.random() < 0.4:
        return {
            "bundle_id":          ANOMALY_BUNDLE,
            "escalation_reason":  "prior violation pattern — repeated underdeclaration of data types",
            "reviewer_confidence":round(rng.uniform(0.2, 0.45), 2),
            "policy_sections_cited": ["5.1.1 Data Collection and Storage",
                                      "5.1.2 Data Use and Sharing"],
            "recommended_disposition": None,
            "urgency":            "high",
        }
    return escalation_normal(ctx)


# ── Wire up ──────────────────────────────────────────────────────────────────

def make_streams(tick_interval, anomaly_delay, intensity, seed,
                 anomaly_duration=0.0, anomaly_cycle_interval=0.0):
    def mk(name, ngen, agen, tick_rate=1):
        return EventStream(
            source=SignalSource(name=name, normal_gen=ngen, anomaly_gen=agen, tick_rate=tick_rate),
            tick_interval=tick_interval, anomaly_delay=anomaly_delay,
            intensity=intensity, seed=seed,
            anomaly_duration=anomaly_duration,
            anomaly_cycle_interval=anomaly_cycle_interval,
        )
    return [
        mk("submission-queue",   submission_normal,  submission_anomaly),
        mk("policy-kb",          policy_kb_normal,   policy_kb_anomaly,   tick_rate=2),
        mk("submission-history", history_normal,     history_anomaly,     tick_rate=3),
        mk("escalation-queue",   escalation_normal,  escalation_anomaly,  tick_rate=4),
    ]


cli = make_cli(
    use_case="UC2 — App Store Policy Compliance Agent",
    title="Techcompany Simulator: UC2 App Store Compliance",
    streams_factory=make_streams,
)
