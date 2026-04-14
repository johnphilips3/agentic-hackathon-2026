"""
Shared CLI entry point factory and common fake-data helpers.
"""
from __future__ import annotations

import random
from typing import Sequence

import click
import uvicorn
from faker import Faker

from techcompany_sim.core.stream import AnomalyIntensity, EventStream
from techcompany_sim.core.router import build_app

fake = Faker()
Faker.seed(0)

# ── Common reference data ────────────────────────────────────────────────────

GEOGRAPHIES = [
    "US-West", "US-East", "EU-West", "EU-Central", "APAC-East",
    "APAC-South", "LATAM", "MEA",
]

DEVICE_MODELS = [
    "Handset Pro 15", "Handset Pro 15 Max", "Handset 15",
    "Handset Pro 14", "Handset 14",
    "Tablet Pro 13", "Tablet Air 6", "Tablet 10",
    "Notebook Pro 16", "Notebook Air M3",
    "Watch Ultra 2", "Watch Series 9",
    "Earbuds Pro 2", "Earbuds 3",
    "Media Box 4K", "Speaker Mini 2",
]

FIRMWARE_VERSIONS = [
    "17.4.1", "17.5.0", "17.5.1", "17.6.0-beta",
    "14.5.0", "14.6.0",
]

OS_VERSIONS = ["17.4", "17.5", "17.5.1", "17.6b", "16.7.8"]

COMPONENT_TYPES = [
    "battery", "display", "camera-module", "haptic-engine",
    "cellular-modem", "wifi-chip", "touch-controller",
    "power-management-ic", "speaker-assembly", "face-id-module",
]


def random_serial_prefix(rng: random.Random) -> str:
    """Manufacturing lot proxy — 4-char prefix."""
    return rng.choice(["F3K", "G4M", "H2P", "J7Q", "K9R", "L1S", "M5T"])


def weighted_choice(rng: random.Random, options: list, weights: list):
    return rng.choices(options, weights=weights, k=1)[0]


# ── CLI factory ──────────────────────────────────────────────────────────────

def make_cli(
    use_case: str,
    title: str,
    streams_factory,          # callable(tick_interval, anomaly_delay, intensity, seed) -> [EventStream]
):
    @click.command()
    @click.option("--port",             default=8000,     show_default=True, help="HTTP port")
    @click.option("--host",             default="0.0.0.0",show_default=True, help="Bind host")
    @click.option("--tick-interval",    default=2.0,      show_default=True, help="Seconds between event ticks")
    @click.option("--anomaly-delay",    default=120.0,    show_default=True, help="Seconds after startup before anomaly activates")
    @click.option("--anomaly-intensity",
                  default="moderate",
                  type=click.Choice(["subtle", "moderate", "obvious"]),
                  show_default=True,
                  help="How pronounced the seeded anomaly is")
    @click.option("--seed",             default=42,       show_default=True, help="RNG seed for reproducible runs")
    def cli(port, host, tick_interval, anomaly_delay, anomaly_intensity, seed):
        """Techcompany hackathon data simulator — %(use_case)s""" % {"use_case": use_case}

        intensity = AnomalyIntensity(anomaly_intensity)
        streams   = streams_factory(tick_interval, anomaly_delay, intensity, seed)
        app       = build_app(title=title, streams=streams, use_case=use_case)

        click.echo(f"\n{'='*60}")
        click.echo(f"  Techcompany Simulator: {use_case}")
        click.echo(f"  http://{host}:{port}/docs  ← interactive API docs")
        click.echo(f"  Anomaly activates in {anomaly_delay:.0f}s  |  intensity={anomaly_intensity}")
        click.echo(f"  Tick interval={tick_interval}s  |  seed={seed}")
        click.echo(f"{'='*60}\n")

        uvicorn.run(app, host=host, port=port, log_level="warning")

    return cli
