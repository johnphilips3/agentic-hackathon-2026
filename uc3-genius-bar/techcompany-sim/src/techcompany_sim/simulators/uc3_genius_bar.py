"""
UC3 — Retail Genius Bar Triage and Escalation Agent
Signal sources:
  1. appointment-queue  — incoming Genius Bar appointments
  2. device-diagnostics — telemetry snapshots by serial number
  3. repair-history     — prior service events
  4. parts-scheduling   — parts inventory + technician availability

Seeded anomaly: a batch of Handset Pro 15 units from manufacturing lot J7Q
begins arriving with a recurring haptic-engine failure that has already been
"repaired" once — the repair history shows the same component replaced, but
the failure is recurring faster each time, signalling an underlying design
issue that should trigger depot escalation and an engineering flag.
"""
from __future__ import annotations

import random

from techcompany_sim.core.stream import AnomalyIntensity, EventStream, SignalSource, StreamContext
from techcompany_sim.core.cli import (
    make_cli, DEVICE_MODELS, COMPONENT_TYPES, random_serial_prefix, weighted_choice
)

STORES           = ["SFO-Union-Square", "NYC-Fifth-Ave", "CHI-Michigan-Ave",
                    "LAX-Grove", "LDN-Regent-St", "TYO-Omotesando", "SYD-CBD"]
SYMPTOM_TYPES    = ["battery-drain", "display-flicker", "camera-failure",
                    "haptic-not-working", "wifi-drops", "speaker-distortion",
                    "face-id-failure", "touchscreen-unresponsive", "overheating",
                    "software-crash", "bluetooth-dropout"]
APPOINTMENT_TYPES = ["hardware", "software", "accidental-damage", "setup-support"]
SKILL_LEVELS     = ["standard", "senior", "specialist"]
SERVICE_PATHS    = ["in-store-same-day", "in-store-scheduled", "depot-repair",
                    "express-replacement", "software-only"]

ANOMALY_LOT      = "J7Q"
ANOMALY_MODEL    = "Handset Pro 15"
ANOMALY_SYMPTOM  = "haptic-not-working"
ANOMALY_COMPONENT= "haptic-engine"


def rand_serial(rng: random.Random, lot: str | None = None) -> str:
    prefix = lot or random_serial_prefix(rng)
    return f"{prefix}{rng.randint(100000, 999999)}"


# ── Signal Source 1: Appointment Queue ───────────────────────────────────────

def appointment_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    model = rng.choice(DEVICE_MODELS)
    return {
        "appointment_id":   f"APT-{rng.randint(10000,99999)}",
        "store":            rng.choice(STORES),
        "device_model":     model,
        "serial_prefix":    random_serial_prefix(rng),
        "serial_number":    rand_serial(rng),
        "appointment_type": rng.choice(APPOINTMENT_TYPES),
        "symptom_description": rng.choice(SYMPTOM_TYPES),
        "customer_description": f"Device experiencing {rng.choice(SYMPTOM_TYPES).replace('-',' ')} intermittently",
        "slot_time":        f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(9,18):02d}:00:00",
        "warranty_status":  rng.choice(["in-warranty", "out-of-warranty", "applecare-plus"]),
    }


def appointment_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.5:
        serial = rand_serial(rng, ANOMALY_LOT)
        warranty = {"subtle": "out-of-warranty", "moderate": "out-of-warranty",
                    "obvious": "in-warranty"}[intensity.value]
        return {
            "appointment_id":   f"APT-{rng.randint(10000,99999)}",
            "store":            rng.choice(STORES),
            "device_model":     ANOMALY_MODEL,
            "serial_prefix":    ANOMALY_LOT,
            "serial_number":    serial,
            "appointment_type": "hardware",
            "symptom_description": ANOMALY_SYMPTOM,
            "customer_description": "Haptic feedback completely stopped working — phone feels dead",
            "slot_time":        f"2024-{rng.randint(10,12):02d}-{rng.randint(1,28):02d}T{rng.randint(9,17):02d}:00:00",
            "warranty_status":  warranty,
        }
    return appointment_normal(ctx)


# ── Signal Source 2: Device Diagnostics ──────────────────────────────────────

def diagnostics_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    serial = rand_serial(rng)
    return {
        "serial_number":       serial,
        "device_model":        rng.choice(DEVICE_MODELS),
        "battery_health_pct":  rng.randint(72, 100),
        "battery_cycles":      rng.randint(50, 600),
        "crash_log_flags":     rng.randint(0, 3),
        "storage_health":      rng.choice(["good", "good", "good", "degraded"]),
        "last_diagnostic_pass":rng.random() > 0.1,
        "flagged_components":  [],
        "os_version":          rng.choice(["17.4", "17.5", "17.5.1"]),
    }


def diagnostics_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        crash_flags  = {"subtle": rng.randint(2, 4), "moderate": rng.randint(5, 10),
                        "obvious": rng.randint(12, 25)}[intensity.value]
        diag_pass    = {"subtle": True, "moderate": False, "obvious": False}[intensity.value]
        return {
            "serial_number":       rand_serial(rng, ANOMALY_LOT),
            "device_model":        ANOMALY_MODEL,
            "battery_health_pct":  rng.randint(88, 100),   # battery fine — not the issue
            "battery_cycles":      rng.randint(30, 120),
            "crash_log_flags":     crash_flags,
            "storage_health":      "good",
            "last_diagnostic_pass":diag_pass,
            "flagged_components":  [ANOMALY_COMPONENT],
            "os_version":          "17.5.1",
        }
    return diagnostics_normal(ctx)


# ── Signal Source 3: Repair History ──────────────────────────────────────────

REPAIR_TYPES  = ["component-replacement", "software-restore", "board-level-repair",
                 "cosmetic-repair", "express-replacement-issued"]
OUTCOMES_REP  = ["resolved", "resolved", "resolved", "unresolved", "recurring"]


def repair_history_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    outcome = rng.choice(OUTCOMES_REP)
    return {
        "serial_number":    rand_serial(rng),
        "device_model":     rng.choice(DEVICE_MODELS),
        "repair_date":      f"2024-{rng.randint(1,10):02d}-{rng.randint(1,28):02d}",
        "repair_type":      rng.choice(REPAIR_TYPES),
        "component_replaced": rng.choice(COMPONENT_TYPES) if "component" in rng.choice(REPAIR_TYPES) else None,
        "technician_notes": f"Standard repair completed. {rng.choice(['Customer satisfied.','Issue confirmed and resolved.','Follow-up may be needed.'])}",
        "outcome":          outcome,
        "store":            rng.choice(STORES),
        "days_since_repair":rng.randint(0, 365),
    }


def repair_history_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.5:
        days = {"subtle": rng.randint(60, 120), "moderate": rng.randint(20, 60),
                "obvious": rng.randint(5, 20)}[intensity.value]
        return {
            "serial_number":    rand_serial(rng, ANOMALY_LOT),
            "device_model":     ANOMALY_MODEL,
            "repair_date":      f"2024-{rng.randint(7,10):02d}-{rng.randint(1,28):02d}",
            "repair_type":      "component-replacement",
            "component_replaced": ANOMALY_COMPONENT,
            "technician_notes": f"Haptic engine replaced. Unit returned to customer. Failure recurred after {days} days.",
            "outcome":          "recurring",
            "store":            rng.choice(STORES),
            "days_since_repair":days,
        }
    return repair_history_normal(ctx)


# ── Signal Source 4: Parts and Scheduling ────────────────────────────────────

def parts_scheduling_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    component = rng.choice(COMPONENT_TYPES)
    device    = rng.choice(DEVICE_MODELS)
    return {
        "component_type":        component,
        "device_model":          device,
        "store":                 rng.choice(STORES),
        "units_on_hand":         rng.randint(0, 30),
        "estimated_restock_days":rng.randint(1, 14) if rng.random() > 0.2 else None,
        "available_slots": {
            skill: rng.randint(0, 5) for skill in SKILL_LEVELS
        },
        "recommended_service_path": rng.choice(SERVICE_PATHS),
    }


def parts_scheduling_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    if rng.random() < 0.55:
        units = {"subtle": rng.randint(3, 8), "moderate": rng.randint(0, 2),
                 "obvious": 0}[intensity.value]
        restock = {"subtle": rng.randint(5, 10), "moderate": rng.randint(14, 28),
                   "obvious": None}[intensity.value]
        path    = {"subtle": "in-store-scheduled", "moderate": "depot-repair",
                   "obvious": "depot-repair"}[intensity.value]
        return {
            "component_type":        ANOMALY_COMPONENT,
            "device_model":          ANOMALY_MODEL,
            "store":                 rng.choice(STORES),
            "units_on_hand":         units,
            "estimated_restock_days":restock,
            "available_slots": {
                "standard":   rng.randint(0, 3),
                "senior":     rng.randint(0, 2),
                "specialist": rng.randint(0, 1),
            },
            "recommended_service_path": path,
        }
    return parts_scheduling_normal(ctx)


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
        mk("appointment-queue",  appointment_normal,      appointment_anomaly),
        mk("device-diagnostics", diagnostics_normal,      diagnostics_anomaly),
        mk("repair-history",     repair_history_normal,   repair_history_anomaly, tick_rate=2),
        mk("parts-scheduling",   parts_scheduling_normal, parts_scheduling_anomaly, tick_rate=2),
    ]


cli = make_cli(
    use_case="UC3 — Retail Genius Bar Triage and Escalation Agent",
    title="Techcompany Simulator: UC3 Genius Bar",
    streams_factory=make_streams,
)
