"""
Offline seed data generator.

Runs any simulator's signal sources in fast-forward (no real sleep) and
writes one JSON file per source. The anomaly activates at the midpoint of
the simulated duration by default, so every output file contains both
baseline and anomaly events.

Entry points (registered in pyproject.toml):
    sim-generate-uc1  through  sim-generate-uc5
    sim-generate-all  — generates all five use cases in one shot
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import click

from techcompany_sim.core.stream import AnomalyIntensity, SignalSource, StreamContext, Event


# ── Fast-forward engine ──────────────────────────────────────────────────────

@dataclass
class GeneratorConfig:
    use_case:        str
    slug:            str          # used in output filenames, e.g. "uc1"
    sources_factory: Callable    # same factory signature as the live simulators


def generate(
    config: GeneratorConfig,
    duration: float,
    tick_interval: float,
    anomaly_delay: float,
    intensity: AnomalyIntensity,
    seed: int,
    output_dir: Path,
) -> dict[str, int]:
    """
    Simulate `duration` seconds of wall-clock time in fast-forward.
    Returns {source_name: event_count} for the summary line.
    """
    import random
    rng = random.Random(seed)

    # Build sources (we only need the SignalSource definitions, not full EventStream)
    streams = config.sources_factory(tick_interval, anomaly_delay, intensity, seed)
    sources: list[SignalSource] = [s.source for s in streams]

    total_ticks   = int(duration / tick_interval)
    sim_start     = 0.0     # simulated clock starts at 0
    counts: dict[str, int] = {s.name: 0 for s in sources}
    buffers: dict[str, list] = {s.name: [] for s in sources}

    for tick in range(1, total_ticks + 1):
        elapsed        = tick * tick_interval
        sim_timestamp  = time.time() - duration + elapsed   # realistic unix ts
        anomaly_active = elapsed >= anomaly_delay

        ctx = StreamContext(
            tick=tick,
            elapsed=elapsed,
            anomaly_active=anomaly_active,
            intensity=intensity,
            rng=rng,
        )

        for source in sources:
            if tick % source.tick_rate != 0:
                continue

            gen  = source.anomaly_gen if anomaly_active else source.normal_gen
            data = gen(ctx)
            if data is None:
                continue

            event = Event(
                id=str(uuid.uuid4()),
                source=source.name,
                timestamp=sim_timestamp,
                data=data,
                is_anomaly=anomaly_active,
            )
            buffers[source.name].append(event.to_dict())
            counts[source.name] += 1

    # Write output files
    output_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        fname = output_dir / f"{config.slug}-{source.name}.json"
        payload = {
            "use_case":       config.use_case,
            "source":         source.name,
            "generated_at":   time.time(),
            "duration_seconds": duration,
            "tick_interval":  tick_interval,
            "anomaly_delay":  anomaly_delay,
            "anomaly_intensity": intensity.value,
            "seed":           seed,
            "event_count":    counts[source.name],
            "events":         buffers[source.name],
        }
        with open(fname, "w") as f:
            json.dump(payload, f, indent=2)

    return counts


# ── CLI factory ───────────────────────────────────────────────────────────────

COMMON_OPTIONS = [
    click.option("--duration",          default=600.0,    show_default=True,
                 help="Simulated duration in seconds"),
    click.option("--tick-interval",     default=2.0,      show_default=True,
                 help="Seconds between ticks (controls event density)"),
    click.option("--anomaly-delay",     default=None,     type=float,
                 help="Seconds before anomaly activates (default: half of duration)"),
    click.option("--anomaly-intensity", default="moderate",
                 type=click.Choice(["subtle", "moderate", "obvious"]), show_default=True),
    click.option("--seed",              default=42,        show_default=True,
                 help="RNG seed for reproducible output"),
    click.option("--output",            default="./seed-data", show_default=True,
                 help="Output directory for JSON files"),
]


def add_options(options):
    def decorator(f):
        for option in reversed(options):
            f = option(f)
        return f
    return decorator


def make_generate_cli(config: GeneratorConfig):
    @click.command(name=f"sim-generate-{config.slug}")
    @add_options(COMMON_OPTIONS)
    def cmd(duration, tick_interval, anomaly_delay, anomaly_intensity, seed, output):
        f"""Generate static seed data for {config.use_case}."""
        delay     = anomaly_delay if anomaly_delay is not None else duration / 2
        intensity = AnomalyIntensity(anomaly_intensity)
        out_dir   = Path(output)

        click.echo(f"\nGenerating seed data: {config.use_case}")
        click.echo(f"  Duration:        {duration:.0f}s  ({duration/60:.1f} min simulated)")
        click.echo(f"  Tick interval:   {tick_interval}s")
        click.echo(f"  Anomaly at:      {delay:.0f}s ({delay/duration*100:.0f}% through)")
        click.echo(f"  Intensity:       {anomaly_intensity}")
        click.echo(f"  Seed:            {seed}")
        click.echo(f"  Output dir:      {out_dir.resolve()}\n")

        t0     = time.time()
        counts = generate(config, duration, tick_interval, intensity, seed, out_dir,
                          anomaly_delay=delay)
        elapsed = time.time() - t0

        click.echo("Files written:")
        for source, count in counts.items():
            fname = out_dir / f"{config.slug}-{source}.json"
            click.echo(f"  {fname}  ({count} events)")
        click.echo(f"\nDone in {elapsed:.2f}s")

    return cmd


# There's a parameter order mismatch in generate() — fix it here
def generate(
    config: GeneratorConfig,
    duration: float,
    tick_interval: float,
    intensity: AnomalyIntensity,
    seed: int,
    output_dir: Path,
    anomaly_delay: float | None = None,
) -> dict[str, int]:
    import random
    rng = random.Random(seed)
    delay = anomaly_delay if anomaly_delay is not None else duration / 2

    streams = config.sources_factory(tick_interval, delay, intensity, seed)
    sources: list[SignalSource] = [s.source for s in streams]

    total_ticks = int(duration / tick_interval)
    counts:  dict[str, int]    = {s.name: 0  for s in sources}
    buffers: dict[str, list]   = {s.name: [] for s in sources}

    base_ts = time.time() - duration   # events get realistic unix timestamps

    for tick in range(1, total_ticks + 1):
        elapsed        = tick * tick_interval
        sim_timestamp  = base_ts + elapsed
        anomaly_active = elapsed >= delay

        ctx = StreamContext(
            tick=tick,
            elapsed=elapsed,
            anomaly_active=anomaly_active,
            intensity=intensity,
            rng=rng,
        )

        for source in sources:
            if tick % source.tick_rate != 0:
                continue
            gen  = source.anomaly_gen if anomaly_active else source.normal_gen
            data = gen(ctx)
            if data is None:
                continue
            event = Event(
                id=str(uuid.uuid4()),
                source=source.name,
                timestamp=sim_timestamp,
                data=data,
                is_anomaly=anomaly_active,
            )
            buffers[source.name].append(event.to_dict())
            counts[source.name] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        fname = output_dir / f"{config.slug}-{source.name}.json"
        payload = {
            "use_case":          config.use_case,
            "source":            source.name,
            "generated_at":      time.time(),
            "duration_seconds":  duration,
            "tick_interval":     tick_interval,
            "anomaly_delay":     delay,
            "anomaly_intensity": intensity.value,
            "seed":              seed,
            "event_count":       counts[source.name],
            "events":            buffers[source.name],
        }
        with open(fname, "w") as f:
            json.dump(payload, f, indent=2)

    return counts


# ── UC1 CLI commands ─────────────────────────────────────────────────────────

def _uc1_config():
    from techcompany_sim.simulators.uc1_supply_chain import make_streams as uc1
    return GeneratorConfig("UC1 — Supply Chain Disruption Response Agent", "uc1", uc1)


def cli_generate_uc1():
    make_generate_cli(_uc1_config())()


# ── UC2 CLI commands ─────────────────────────────────────────────────────────

def _uc2_config():
    from techcompany_sim.simulators.uc2_app_store import make_streams as uc2
    return GeneratorConfig("UC2 — App Store Policy Compliance Agent", "uc2", uc2)


def cli_generate_uc2():
    make_generate_cli(_uc2_config())()


# ── UC3 CLI commands ─────────────────────────────────────────────────────────

def _uc3_config():
    from techcompany_sim.simulators.uc3_genius_bar import make_streams as uc3
    return GeneratorConfig("UC3 — Retail Genius Bar Triage and Escalation Agent", "uc3", uc3)


def cli_generate_uc3():
    make_generate_cli(_uc3_config())()


# ── UC4 CLI commands ─────────────────────────────────────────────────────────

def _uc4_config():
    from techcompany_sim.simulators.uc4_devrel import make_streams as uc4
    return GeneratorConfig("UC4 — Developer Relations Insights Agent", "uc4", uc4)


def cli_generate_uc4():
    make_generate_cli(_uc4_config())()


# ── UC5 CLI commands ─────────────────────────────────────────────────────────

def _uc5_config():
    from techcompany_sim.simulators.uc5_hardware import make_streams as uc5
    return GeneratorConfig("UC5 — Hardware Failure Pattern Detection and Field Action Agent", "uc5", uc5)


def cli_generate_uc5():
    make_generate_cli(_uc5_config())()