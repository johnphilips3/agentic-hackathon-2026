# Techcompany Simulator Core

Core modules for the Techcompany hackathon data simulator. This package provides the shared infrastructure used by all use case simulators.

## What's Inside

- **stream.py**: Event stream management with anomaly injection
- **router.py**: FastAPI route registration for signal sources
- **cli.py**: Shared CLI functionality
- **generator.py**: Offline seed data generation

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
