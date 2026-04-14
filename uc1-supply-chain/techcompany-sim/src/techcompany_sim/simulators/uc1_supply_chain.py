"""
UC1 — Supply Chain Disruption Response Agent
Signal sources:
  1. supplier-capacity   — tier-1/2 supplier capacity and quality events
  2. logistics           — freight and port status events
  3. geopolitical        — news events tagged by geography and supply-chain relevance
  4. inventory           — internal component inventory snapshots

Seeded anomaly: a critical APAC-East supplier (lot prefix J7Q) experiences
a cascading capacity collapse driven by a geopolitical export restriction,
triggering a logistics congestion spike and revealing dangerously low
inventory coverage for the cellular-modem component used in Handset Pro 15.
"""
from __future__ import annotations

import random

from techcompany_sim.core.stream import AnomalyIntensity, EventStream, SignalSource, StreamContext
from techcompany_sim.core.cli import (
    make_cli, GEOGRAPHIES, COMPONENT_TYPES, random_serial_prefix, weighted_choice
)

# ── Signal Source 1: Supplier Capacity ──────────────────────────────────────

SUPPLIERS = [
    "Apex Components Ltd", "Helix Manufacturing", "NovaTech Industries",
    "PrimeParts Co", "Stellar Supply Group", "CoreFab International",
    "UltraComponents", "PeakPrecision Ltd",
]
CAPACITY_EVENTS = ["planned-downtime", "quality-hold", "workforce-reduction",
                   "capacity-expansion", "shift-change", "equipment-maintenance"]
ANOMALY_SUPPLIER = "CoreFab International"   # the one that collapses


def supplier_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "supplier":        rng.choice(SUPPLIERS),
        "tier":            rng.choice([1, 1, 1, 2, 2]),
        "geography":       rng.choice(GEOGRAPHIES),
        "component_type":  rng.choice(COMPONENT_TYPES),
        "event_type":      weighted_choice(rng, CAPACITY_EVENTS, [5, 3, 2, 8, 6, 4]),
        "capacity_pct":    round(rng.gauss(88, 6), 1),
        "quality_yield_pct": round(rng.gauss(97, 1.5), 2),
        "workforce_available_pct": round(rng.gauss(95, 3), 1),
        "notes":           None,
    }


def supplier_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity

    # Cascade: capacity drops, yield collapses, workforce flags
    capacity_drop = {"subtle": 15, "moderate": 35, "obvious": 60}[intensity.value]
    yield_drop    = {"subtle": 2,  "moderate": 8,  "obvious": 18}[intensity.value]

    if rng.random() < 0.6:   # 60% of anomaly ticks feature the bad supplier
        return {
            "supplier":       ANOMALY_SUPPLIER,
            "tier":           1,
            "geography":      "APAC-East",
            "component_type": "cellular-modem",
            "event_type":     rng.choice(["quality-hold", "workforce-reduction", "planned-downtime"]),
            "capacity_pct":   round(max(5, rng.gauss(88 - capacity_drop, 4)), 1),
            "quality_yield_pct": round(max(60, rng.gauss(97 - yield_drop, 2)), 2),
            "workforce_available_pct": round(max(30, rng.gauss(95 - capacity_drop * 0.5, 5)), 1),
            "notes":          "EXPORT RESTRICTION IMPACT — production severely constrained",
        }
    return supplier_normal(ctx)


# ── Signal Source 2: Logistics ───────────────────────────────────────────────

CARRIERS     = ["AirFreight Global", "OceanLink", "SwiftCargo", "PrimeLift Air", "TransPac Shipping"]
DELAY_CAUSES = ["port-congestion", "customs-hold", "weather", "carrier-capacity", "none", "none", "none"]


def logistics_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "carrier":           rng.choice(CARRIERS),
        "mode":              weighted_choice(rng, ["air", "ocean", "ground"], [3, 5, 2]),
        "origin":            rng.choice(GEOGRAPHIES),
        "destination":       rng.choice(GEOGRAPHIES),
        "component_type":    rng.choice(COMPONENT_TYPES),
        "status":            weighted_choice(rng, ["on-time", "delayed", "arrived", "departed"], [7, 2, 4, 4]),
        "delay_hours":       max(0, round(rng.gauss(0, 4))),
        "delay_cause":       rng.choice(DELAY_CAUSES),
        "port_congestion_index": round(rng.uniform(0.1, 0.4), 2),
    }


def logistics_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity
    congestion_spike = {"subtle": 0.25, "moderate": 0.45, "obvious": 0.65}[intensity.value]

    if rng.random() < 0.55:
        return {
            "carrier":           rng.choice(CARRIERS),
            "mode":              "ocean",
            "origin":            "APAC-East",
            "destination":       rng.choice(["US-West", "EU-West"]),
            "component_type":    "cellular-modem",
            "status":            "delayed",
            "delay_hours":       rng.randint(48, 240),
            "delay_cause":       "port-congestion",
            "port_congestion_index": round(min(1.0, rng.uniform(
                0.6 + congestion_spike * 0.2, 0.7 + congestion_spike
            )), 2),
        }
    return logistics_normal(ctx)


# ── Signal Source 3: Geopolitical ───────────────────────────────────────────

EVENT_TYPES = ["export-control", "labor-unrest", "natural-disaster",
               "regulatory-change", "political-transition", "trade-dispute"]
SEVERITIES  = ["low", "medium", "high", "critical"]
CATEGORIES  = ["semiconductor", "raw-materials", "logistics", "energy", "labor"]


def geopolitical_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "headline":      f"{fake_headline(rng, 'normal')}",
        "geography":     rng.choice(GEOGRAPHIES),
        "event_type":    weighted_choice(rng, EVENT_TYPES, [2, 3, 1, 4, 2, 3]),
        "severity":      weighted_choice(rng, SEVERITIES, [5, 4, 2, 1]),
        "sc_relevance":  rng.choice(CATEGORIES),
        "confidence":    round(rng.uniform(0.5, 0.95), 2),
        "source":        rng.choice(["Reuters Synthesis", "Trade Monitor", "Risk Pulse", "Geo Intel Feed"]),
    }


def geopolitical_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity
    severity  = {"subtle": "high", "moderate": "high", "obvious": "critical"}[intensity.value]

    if rng.random() < 0.5:
        return {
            "headline":     "APAC-East government imposes emergency semiconductor export restrictions targeting advanced modem components",
            "geography":    "APAC-East",
            "event_type":   "export-control",
            "severity":     severity,
            "sc_relevance": "semiconductor",
            "confidence":   round(rng.uniform(0.82, 0.99), 2),
            "source":       "Trade Monitor",
        }
    return geopolitical_normal(ctx)


def fake_headline(rng: random.Random, mode: str) -> str:
    templates = [
        "Regional {adj} impacts {cat} supply chains in {geo}",
        "{geo} announces new {cat} regulations affecting imports",
        "Labor dispute at {geo} manufacturing hubs enters week {n}",
        "{geo} port authority reports {adj} throughput conditions",
        "Trade analysts flag {adj} risk in {geo} {cat} sector",
    ]
    geo  = rng.choice(["APAC", "EU", "LATAM", "MEA", "US"])
    adj  = rng.choice(["elevated", "moderate", "significant", "manageable", "improving"])
    cat  = rng.choice(["semiconductor", "logistics", "energy", "raw-material"])
    n    = rng.randint(1, 8)
    tmpl = rng.choice(templates)
    return tmpl.format(adj=adj, cat=cat, geo=geo, n=n)


# ── Signal Source 4: Inventory ───────────────────────────────────────────────

WAREHOUSES = ["SJC-1", "AMS-2", "SHA-3", "DFW-4", "LHR-5"]


def inventory_normal(ctx: StreamContext) -> dict:
    rng = ctx.rng
    return {
        "component_type":  rng.choice(COMPONENT_TYPES),
        "warehouse":       rng.choice(WAREHOUSES),
        "units_on_hand":   rng.randint(50_000, 800_000),
        "days_of_supply":  round(rng.uniform(25, 90), 1),
        "reorder_point":   rng.randint(20_000, 100_000),
        "in_transit_units":rng.randint(5_000, 200_000),
        "alert":           None,
    }


def inventory_anomaly(ctx: StreamContext) -> dict:
    rng = ctx.rng
    intensity = ctx.intensity
    dos_floor = {"subtle": 12, "moderate": 6, "obvious": 2}[intensity.value]

    if rng.random() < 0.65:
        days = round(rng.uniform(dos_floor * 0.5, dos_floor), 1)
        return {
            "component_type":   "cellular-modem",
            "warehouse":        rng.choice(["SJC-1", "AMS-2"]),
            "units_on_hand":    rng.randint(800, 8000),
            "days_of_supply":   days,
            "reorder_point":    45_000,
            "in_transit_units": 0,
            "alert":            f"CRITICAL: {days} days of supply remaining — replenishment pipeline disrupted",
        }
    return inventory_normal(ctx)


# ── Wire up ──────────────────────────────────────────────────────────────────

def make_streams(tick_interval, anomaly_delay, intensity, seed):
    def mk(name, ngen, agen, tick_rate=1):
        return EventStream(
            source=SignalSource(name=name, normal_gen=ngen, anomaly_gen=agen, tick_rate=tick_rate),
            tick_interval=tick_interval,
            anomaly_delay=anomaly_delay,
            intensity=intensity,
            seed=seed,
        )
    return [
        mk("supplier-capacity", supplier_normal, supplier_anomaly),
        mk("logistics",         logistics_normal, logistics_anomaly),
        mk("geopolitical",      geopolitical_normal, geopolitical_anomaly, tick_rate=3),
        mk("inventory",         inventory_normal,  inventory_anomaly,  tick_rate=2),
    ]


cli = make_cli(
    use_case="UC1 — Supply Chain Disruption Response Agent",
    title="Techcompany Simulator: UC1 Supply Chain",
    streams_factory=make_streams,
)
