"""
UC4 — Developer Relations Insights Agent
Signal sources:
  1. forum-feed          — developer forum posts and replies
  2. appstore-connect    — App Store Connect feedback and crash reports
  3. crash-trends        — weekly SDK crash rate trend summaries
  4. wwdc-engagement     — WWDC session view/completion metrics

Seeded anomaly: a newly introduced Vision framework update (VisionKit 4.2)
is causing a sharp and accelerating crash rate spike across apps using the
new spatial audio APIs on visionOS, while forum posts cluster around the
same error domain. WWDC session completion for the relevant session drops
simultaneously, signalling broad developer confusion rather than an isolated bug.
"""
from __future__ import annotations

import random

from techcompany_sim.core.stream import AnomalyIntensity, EventStream, SignalSource, StreamContext
from techcompany_sim.core.cli import make_cli, DEVICE_MODELS, OS_VERSIONS, weighted_choice

FRAMEWORKS    = ["SwiftUI", "UIKit", "CoreML", "ARKit", "VisionKit", "HealthKit",
                 "CloudKit", "StoreKit", "MapKit", "AVFoundation", "CoreBluetooth",
                 "PassKit", "WatchConnectivity", "RealityKit", "SpatialAudio"]
PLATFORMS     = ["iOS", "macOS", "watchOS", "tvOS", "visionOS"]
POST_TYPES    = ["question", "bug-report", "feature-request", "complaint", "discussion"]
SENTIMENTS    = ["positive", "neutral", "neutral", "negative", "very-negative"]
SDK_VERSIONS  = ["4.0", "4.1", "4.2", "4.3-beta", "3.9"]
WWDC_SESSIONS = [
    "Introducing VisionKit 4.2",
    "Spatial Audio APIs for visionOS",
    "Building with SwiftUI 6",
    "CoreML on-device performance",
    "StoreKit 2 migration guide",
    "App Intents deep dive",
    "Swift concurrency in practice",
    "ARKit scene reconstruction",
]
ENGAGEMENT_FLOOR = 0.45   # normal min completion rate

ANOMALY_FRAMEWORK = "VisionKit"
ANOMALY_SDK       = "4.2"
ANOMALY_PLATFORM  = "visionOS"
ANOMALY_SESSION   = "Introducing VisionKit 4.2"
ANOMALY_SESSION2  = "Spatial Audio APIs for visionOS"


# ── Signal Source 1: Forum Feed ───────────────────────────────────────────────

FORUM_TEMPLATES = [
    "How do I {action} using {fw} on {platform}?",
    "{fw} {action} not working after updating to SDK {ver}",
    "Anyone else seeing {fw} crash logs with {err}?",
    "Best practice for {action} with {fw} in {platform}?",
    "{fw} documentation seems out of date for SDK {ver}",
    "Resolved: {action} with {fw} — sharing solution",
]
ACTIONS = ["handle background tasks", "implement deep linking", "manage state",
           "integrate payments", "request permissions", "render 3D content",
           "sync data", "authenticate users", "stream media", "process images"]
ERRORS  = ["EXC_BAD_ACCESS", "SIGABRT", "NSInternalInconsistencyException",
           "memory pressure termination", "thread violation assertion"]


def forum_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    fw  = rng.choice(FRAMEWORKS)
    return {
        "post_id":          f"POST-{rng.randint(100000,999999)}",
        "framework":        fw,
        "platform":         rng.choice(PLATFORMS),
        "sdk_version":      rng.choice(SDK_VERSIONS),
        "post_type":        weighted_choice(rng, POST_TYPES, [4, 3, 2, 2, 1]),
        "sentiment":        weighted_choice(rng, SENTIMENTS, [2, 4, 3, 2, 1]),
        "title":            rng.choice(FORUM_TEMPLATES).format(
            action=rng.choice(ACTIONS), fw=fw, platform=rng.choice(PLATFORMS),
            ver=rng.choice(SDK_VERSIONS), err=rng.choice(ERRORS),
        ),
        "view_count":       rng.randint(20, 4000),
        "reply_count":      rng.randint(0, 40),
        "helpful_votes":    rng.randint(0, 80),
        "resolved":         rng.random() > 0.6,
    }


def forum_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.5:
        views    = {"subtle": rng.randint(200, 800), "moderate": rng.randint(800, 3000),
                    "obvious": rng.randint(3000, 12000)}[intensity.value]
        replies  = {"subtle": rng.randint(5, 15), "moderate": rng.randint(15, 40),
                    "obvious": rng.randint(40, 120)}[intensity.value]
        title    = rng.choice([
            f"VisionKit 4.2 spatial audio crashing on visionOS — EXC_BAD_ACCESS in SpatialAudio framework",
            f"Anyone else getting VisionKit 4.2 crashes? Thread started after WWDC session",
            f"CRITICAL: VisionKit 4.2 crash rate spike in production — spatial audio APIs broken",
            f"VisionKit update 4.2 regression: spatial audio session fails on device",
        ])
        return {
            "post_id":      f"POST-{rng.randint(100000,999999)}",
            "framework":    ANOMALY_FRAMEWORK,
            "platform":     ANOMALY_PLATFORM,
            "sdk_version":  ANOMALY_SDK,
            "post_type":    rng.choice(["bug-report", "complaint"]),
            "sentiment":    rng.choice(["negative", "very-negative"]),
            "title":        title,
            "view_count":   views,
            "reply_count":  replies,
            "helpful_votes":rng.randint(replies // 2, replies * 2),
            "resolved":     False,
        }
    return forum_normal(ctx)


# ── Signal Source 2: App Store Connect Feedback ───────────────────────────────

FEEDBACK_TYPES   = ["rejection-appeal", "crash-report", "iap-issue",
                    "metadata-question", "testflight-issue"]
APP_CATEGORIES   = ["Games", "Productivity", "Entertainment", "AR/VR", "Health"]
INSTALL_TIERS    = ["indie", "mid-market", "enterprise"]


def asc_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "feedback_id":      f"ASC-{rng.randint(10000,99999)}",
        "feedback_type":    rng.choice(FEEDBACK_TYPES),
        "app_category":     rng.choice(APP_CATEGORIES),
        "platform":         rng.choice(PLATFORMS),
        "framework_cited":  rng.choice(FRAMEWORKS),
        "sdk_version":      rng.choice(SDK_VERSIONS),
        "install_tier":     rng.choice(INSTALL_TIERS),
        "device_model":     rng.choice(DEVICE_MODELS),
        "os_version":       rng.choice(OS_VERSIONS),
        "crash_rate_pct":   round(rng.uniform(0.01, 0.8), 3),
        "urgency":          weighted_choice(rng, ["low", "medium", "high"], [5, 3, 2]),
    }


def asc_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.45:
        crash_rate = {"subtle": round(rng.uniform(1.2, 2.5), 3),
                      "moderate": round(rng.uniform(3.0, 6.0), 3),
                      "obvious": round(rng.uniform(8.0, 18.0), 3)}[intensity.value]
        return {
            "feedback_id":    f"ASC-{rng.randint(10000,99999)}",
            "feedback_type":  "crash-report",
            "app_category":   "AR/VR",
            "platform":       ANOMALY_PLATFORM,
            "framework_cited":ANOMALY_FRAMEWORK,
            "sdk_version":    ANOMALY_SDK,
            "install_tier":   rng.choice(INSTALL_TIERS),
            "device_model":   "Vision Pro",
            "os_version":     "visionOS 1.2",
            "crash_rate_pct": crash_rate,
            "urgency":        "high",
        }
    return asc_normal(ctx)


# ── Signal Source 3: Crash Trends ─────────────────────────────────────────────

def crash_trends_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    fw  = rng.choice(FRAMEWORKS)
    return {
        "framework":          fw,
        "sdk_version":        rng.choice(SDK_VERSIONS),
        "platform":           rng.choice(PLATFORMS),
        "crash_rate_pct":     round(rng.uniform(0.05, 0.9), 3),
        "week_over_week_delta":round(rng.gauss(0, 0.08), 3),
        "affected_app_count": rng.randint(10, 2000),
        "top_crash_signature":f"{fw}.{rng.choice(['init','render','update','sync'])}::{rng.randint(100,999)}",
        "os_version_breakout":{v: round(rng.uniform(0, 0.4), 2) for v in rng.sample(OS_VERSIONS, 3)},
    }


def crash_trends_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.6:
        delta = {"subtle": round(rng.uniform(0.3, 0.8), 3),
                 "moderate": round(rng.uniform(1.2, 2.5), 3),
                 "obvious": round(rng.uniform(3.0, 6.0), 3)}[intensity.value]
        rate  = {"subtle": round(rng.uniform(1.5, 3.0), 3),
                 "moderate": round(rng.uniform(4.0, 8.0), 3),
                 "obvious": round(rng.uniform(10.0, 22.0), 3)}[intensity.value]
        apps  = {"subtle": rng.randint(50, 200), "moderate": rng.randint(200, 800),
                 "obvious": rng.randint(800, 3500)}[intensity.value]
        return {
            "framework":           ANOMALY_FRAMEWORK,
            "sdk_version":         ANOMALY_SDK,
            "platform":            ANOMALY_PLATFORM,
            "crash_rate_pct":      rate,
            "week_over_week_delta":delta,
            "affected_app_count":  apps,
            "top_crash_signature": "VisionKit.SpatialAudioSession.init::443",
            "os_version_breakout": {"visionOS 1.2": rate},
        }
    return crash_trends_normal(ctx)


# ── Signal Source 4: WWDC Engagement ─────────────────────────────────────────

def wwdc_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    session = rng.choice(WWDC_SESSIONS)
    return {
        "session_title":       session,
        "view_count":          rng.randint(5000, 120000),
        "completion_rate":     round(rng.uniform(ENGAGEMENT_FLOOR, 0.88), 2),
        "doc_traffic_delta":   round(rng.gauss(0, 0.06), 3),
        "sample_code_downloads":rng.randint(200, 15000),
        "related_forum_posts": rng.randint(0, 80),
        "platform":            rng.choice(PLATFORMS),
    }


def wwdc_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        completion = {"subtle": round(rng.uniform(0.32, 0.43), 2),
                      "moderate": round(rng.uniform(0.18, 0.30), 2),
                      "obvious": round(rng.uniform(0.06, 0.16), 2)}[intensity.value]
        doc_delta  = {"subtle": round(rng.uniform(0.3, 0.7), 3),
                      "moderate": round(rng.uniform(0.8, 1.5), 3),
                      "obvious": round(rng.uniform(1.8, 3.5), 3)}[intensity.value]
        forum_posts= {"subtle": rng.randint(20, 60), "moderate": rng.randint(60, 180),
                      "obvious": rng.randint(180, 500)}[intensity.value]
        session    = rng.choice([ANOMALY_SESSION, ANOMALY_SESSION2])
        return {
            "session_title":        session,
            "view_count":           rng.randint(8000, 40000),
            "completion_rate":      completion,
            "doc_traffic_delta":    doc_delta,
            "sample_code_downloads":rng.randint(50, 400),
            "related_forum_posts":  forum_posts,
            "platform":             ANOMALY_PLATFORM,
        }
    return wwdc_normal(ctx)


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
        mk("forum-feed",        forum_normal,       forum_anomaly),
        mk("appstore-connect",  asc_normal,         asc_anomaly),
        mk("crash-trends",      crash_trends_normal,crash_trends_anomaly, tick_rate=3),
        mk("wwdc-engagement",   wwdc_normal,        wwdc_anomaly,         tick_rate=4),
    ]


cli = make_cli(
    use_case="UC4 — Developer Relations Insights Agent",
    title="Techcompany Simulator: UC4 Developer Relations",
    streams_factory=make_streams,
)
