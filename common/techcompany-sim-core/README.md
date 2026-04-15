# Techcompany Simulator Core

Core modules for the Techcompany hackathon data simulator. This package provides the shared infrastructure used by all use case simulators.

## What's Inside

- **stream.py**: Event stream management with anomaly injection (permanent, windowed, or cycling)
- **router.py**: FastAPI route registration for signal sources
- **cli.py**: Shared CLI functionality including anomaly mode options
- **generator.py**: Offline seed data generation

## Anomaly Modes

All simulators support three anomaly modes controlled by two optional parameters:

| Mode | `--anomaly-duration` | `--anomaly-cycle-interval` | Behaviour |
|------|---------------------|---------------------------|-----------|
| **Permanent** (default) | `0` (default) | any | One-way latch: anomaly fires at `--anomaly-delay` and runs forever |
| **Single window** | `> 0` | `0` (default) | Anomaly fires for N seconds then stops permanently |
| **Cycling** | `> 0` | `> 0` | Anomaly fires for N seconds, recovers for M seconds, repeats indefinitely |

All existing deployments that omit these parameters behave identically to before (permanent mode).

## Installation

```bash
pip install -e .
```

## Usage

This package is not meant to be used directly. Instead, install a specific use case simulator package that depends on this core:

- techcompany-sim-uc1 (Supply Chain)
- techcompany-sim-uc2 (App Store Policy)
- techcompany-sim-uc3 (Genius Bar)
- techcompany-sim-uc4 (Developer Relations)
- techcompany-sim-uc5 (Hardware Failure)

Each use case simulator will automatically install this core package as a dependency.

## Development

To make changes to the core modules:

1. Edit the source files in `src/techcompany_sim/core/`
2. Reinstall the core package: `pip install -e .`
3. Test with a use case simulator

## Dependencies

- FastAPI >= 0.115.0
- Uvicorn >= 0.30.0
- Click >= 8.1.7
