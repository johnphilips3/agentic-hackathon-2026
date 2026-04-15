"""
UC5 — Hardware Failure Pattern Detection and Field Action Agent
Signal sources:
  1. applecare-cases     — support case records with symptom codes and notes
  2. repair-depot        — structured depot repair reports
  3. warranty-claims     — warranty claim database records
  4. sentiment-feed      — aggregated customer feedback and social signals

Seeded anomaly: Handset Pro 15 Max units from manufacturing lot K9R begin
exhibiting a camera-module failure pattern (specific symptom code CAM-117)
that is silently causing out-of-warranty approvals at an anomalous rate,
while sentiment spikes around "camera" and "photo" complaints on the same
device model. The pattern points to a manufacturing defect in lot K9R that
warrants a Field Action.
"""
from __future__ import annotations

import random

from techcompany_sim.core.stream import AnomalyIntensity, EventStream, SignalSource, StreamContext
from techcompany_sim.core.cli import (
    make_cli, DEVICE_MODELS, GEOGRAPHIES, FIRMWARE_VERSIONS,
    random_serial_prefix, weighted_choice
)

SYMPTOM_CODES = [
    "BAT-001", "BAT-002", "DIS-010", "DIS-015", "CAM-100", "CAM-117",
    "HAP-020", "CEL-030", "WIF-040", "TCH-050", "SPK-060", "FID-070",
    "PWR-080", "BLU-090", "SOS-010",
]
REPAIR_ACTIONS   = ["component-replacement", "board-level-repair", "software-restore",
                    "cosmetic-repair", "no-fault-found", "express-replacement"]
CLAIM_TYPES      = ["in-warranty", "out-of-warranty", "accidental-damage", "applecare-plus"]
SENTIMENT_THEMES = ["battery", "camera", "display", "performance", "overheating",
                    "connectivity", "software", "build-quality", "speaker"]
CHANNELS         = ["app-store-reviews", "support-chat", "social-listening", "nps-survey"]

ANOMALY_LOT     = "K9R"
ANOMALY_MODEL   = "Handset Pro 15 Max"
ANOMALY_SYMPTOM = "CAM-117"
ANOMALY_COMPONENT = "camera-module"


def rand_serial(rng: random.Random, lot: str | None = None) -> str:
    prefix = lot or random_serial_prefix(rng)
    return f"{prefix}{rng.randint(100000,999999)}"


# ── Signal Source 1: Techcompany Care Cases ────────────────────────────────────

TECHNICIAN_NOTES = [
    "Customer reports {symptom}. Confirmed on bench. Component replaced.",
    "Device exhibiting {symptom}. No obvious cause. Returned after software restore.",
    "{symptom} intermittent. Advised customer to monitor.",
    "Escalated to senior technician. {symptom} confirmed. Awaiting parts.",
    "No fault found during diagnostics despite customer reporting {symptom}.",
]


def care_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    symptom = rng.choice(SYMPTOM_CODES)
    return {
        "case_id":         f"CS-{rng.randint(1000000,9999999)}",
        "device_model":    rng.choice(DEVICE_MODELS),
        "serial_prefix":   random_serial_prefix(rng),
        "firmware_version":rng.choice(FIRMWARE_VERSIONS),
        "geography":       rng.choice(GEOGRAPHIES),
        "symptom_code":    symptom,
        "symptom_category":symptom.split("-")[0],
        "technician_notes":rng.choice(TECHNICIAN_NOTES).format(symptom=symptom),
        "case_type":       rng.choice(["phone", "chat", "in-store", "mail-in"]),
        "resolution":      rng.choice(["resolved", "resolved", "resolved", "escalated", "pending"]),
    }


def care_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        resolution = {"subtle": rng.choice(["resolved", "escalated"]),
                      "moderate": "escalated",
                      "obvious": "escalated"}[intensity.value]
        return {
            "case_id":          f"CS-{rng.randint(1000000,9999999)}",
            "device_model":     ANOMALY_MODEL,
            "serial_prefix":    ANOMALY_LOT,
            "firmware_version": rng.choice(["17.5.0", "17.5.1"]),
            "geography":        rng.choice(GEOGRAPHIES),
            "symptom_code":     ANOMALY_SYMPTOM,
            "symptom_category": "CAM",
            "technician_notes": f"Camera module failure confirmed (CAM-117). Rear camera array non-functional. Lot prefix {ANOMALY_LOT}. Component replaced.",
            "case_type":        rng.choice(["in-store", "mail-in"]),
            "resolution":       resolution,
        }
    return care_normal(ctx)


# ── Signal Source 2: Repair Depot Reports ─────────────────────────────────────

def depot_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    action = rng.choice(REPAIR_ACTIONS)
    return {
        "report_id":        f"DEP-{rng.randint(10000,99999)}",
        "device_model":     rng.choice(DEVICE_MODELS),
        "serial_prefix":    random_serial_prefix(rng),
        "component_failed": rng.choice(["camera-module", "battery", "display",
                                         "haptic-engine", "cellular-modem", "speaker"]),
        "failure_code":     rng.choice(SYMPTOM_CODES),
        "repair_action":    action,
        "root_cause":       rng.choice(["customer-damage", "wear", "manufacturing", "software", "unknown"]),
        "parts_consumed":   rng.randint(0, 3),
        "depot_location":   rng.choice(["AUS-Austin", "IRL-Cork", "SGP-Jurong", "CZE-Brno"]),
        "technician_grade": rng.choice(["L1", "L2", "L3"]),
    }


def depot_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.5:
        root = {"subtle": "unknown", "moderate": "manufacturing",
                "obvious": "manufacturing"}[intensity.value]
        return {
            "report_id":       f"DEP-{rng.randint(10000,99999)}",
            "device_model":    ANOMALY_MODEL,
            "serial_prefix":   ANOMALY_LOT,
            "component_failed":ANOMALY_COMPONENT,
            "failure_code":    ANOMALY_SYMPTOM,
            "repair_action":   "component-replacement",
            "root_cause":      root,
            "parts_consumed":  1,
            "depot_location":  rng.choice(["AUS-Austin", "IRL-Cork"]),
            "technician_grade":"L3",
        }
    return depot_normal(ctx)


# ── Signal Source 3: Warranty Claims ──────────────────────────────────────────

def warranty_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    claim_type = rng.choice(CLAIM_TYPES)
    return {
        "claim_id":         f"WC-{rng.randint(1000000,9999999)}",
        "device_model":     rng.choice(DEVICE_MODELS),
        "serial_prefix":    random_serial_prefix(rng),
        "claim_type":       claim_type,
        "symptom_code":     rng.choice(SYMPTOM_CODES),
        "approved":         rng.random() > (0.5 if claim_type == "out-of-warranty" else 0.05),
        "approval_reason":  rng.choice(["policy", "goodwill", "standard", None]),
        "claim_value_usd":  round(rng.uniform(80, 800), 2),
        "geography":        rng.choice(GEOGRAPHIES),
        "device_age_days":  rng.randint(30, 1200),
    }


def warranty_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        # Anomalous out-of-warranty approval rate — symptom of undisclosed defect
        approval_rate = {"subtle": 0.55, "moderate": 0.78, "obvious": 0.95}[intensity.value]
        return {
            "claim_id":         f"WC-{rng.randint(1000000,9999999)}",
            "device_model":     ANOMALY_MODEL,
            "serial_prefix":    ANOMALY_LOT,
            "claim_type":       "out-of-warranty",
            "symptom_code":     ANOMALY_SYMPTOM,
            "approved":         rng.random() < approval_rate,
            "approval_reason":  "goodwill",
            "claim_value_usd":  round(rng.uniform(180, 450), 2),
            "geography":        rng.choice(GEOGRAPHIES),
            "device_age_days":  rng.randint(380, 730),
        }
    return warranty_normal(ctx)


# ── Signal Source 4: Customer Sentiment ───────────────────────────────────────

SENTIMENT_PHRASES = {
    "camera": [
        "Camera completely stopped working out of nowhere",
        "Photos are blurry and the rear camera just fails",
        "Both my friends with the same phone have camera issues",
        "Camera module dead after firmware update — very disappointed",
        "This is a hardware problem not software — camera is toast",
    ],
    "battery": ["Battery draining fast", "Battery fine after update"],
    "display": ["Display looks great", "Screen issues on bright mode"],
}


def sentiment_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    theme   = rng.choice(SENTIMENT_THEMES)
    channel = rng.choice(CHANNELS)
    return {
        "signal_id":        f"SIG-{rng.randint(100000,999999)}",
        "device_model":     rng.choice(DEVICE_MODELS),
        "channel":          channel,
        "theme":            theme,
        "sentiment_score":  round(rng.gauss(0.1, 0.3), 3),  # -1 negative, +1 positive
        "volume_index":     round(rng.uniform(0.1, 0.5), 3),
        "sample_text":      f"General feedback about {theme} on this device.",
        "geography":        rng.choice(GEOGRAPHIES),
    }


def sentiment_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        score  = {"subtle": round(rng.uniform(-0.5, -0.2), 3),
                  "moderate": round(rng.uniform(-0.75, -0.5), 3),
                  "obvious": round(rng.uniform(-0.99, -0.8), 3)}[intensity.value]
        volume = {"subtle": round(rng.uniform(0.5, 0.7), 3),
                  "moderate": round(rng.uniform(0.7, 0.88), 3),
                  "obvious": round(rng.uniform(0.88, 1.0), 3)}[intensity.value]
        return {
            "signal_id":       f"SIG-{rng.randint(100000,999999)}",
            "device_model":    ANOMALY_MODEL,
            "channel":         rng.choice(CHANNELS),
            "theme":           "camera",
            "sentiment_score": score,
            "volume_index":    volume,
            "sample_text":     rng.choice(SENTIMENT_PHRASES["camera"]),
            "geography":       rng.choice(GEOGRAPHIES),
        }
    return sentiment_normal(ctx)


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
        mk("applecare-cases",  care_normal,    care_anomaly),
        mk("repair-depot",     depot_normal,   depot_anomaly),
        mk("warranty-claims",  warranty_normal,warranty_anomaly),
        mk("sentiment-feed",   sentiment_normal,sentiment_anomaly, tick_rate=2),
    ]


cli = make_cli(
    use_case="UC5 — Hardware Failure Pattern Detection and Field Action Agent",
    title="Techcompany Simulator: UC5 Hardware Failure",
    streams_factory=make_streams,
)
