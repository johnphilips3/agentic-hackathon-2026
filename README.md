# Agentic AI Hackathon — Data Simulator

A collection of five independent data simulators for an agentic AI hackathon. Each use case provides continuously streaming signal sources that participant teams use to build autonomous agent systems on Amazon EKS with Amazon Bedrock.

---

## Repository Structure

```
.
├── common/
│   └── techcompany-sim-core/      # Shared FastAPI/SSE core (required by all UC sims)
├── uc1-supply-chain/
│   ├── SCHEMA.md                  # Data schemas for all signal sources
│   └── techcompany-sim/           # Standalone simulator package
├── uc2-app-store/
├── uc3-genius-bar/
├── uc4-devrel/
└── uc5-hardware-failure/
```

Each use case folder is fully self-contained and can be distributed independently without revealing details of other use cases.

---

## Use Cases

| # | Folder | Scenario |
|---|--------|----------|
| 1 | `uc1-supply-chain` | Supply Chain Disruption Response Agent |
| 2 | `uc2-app-store` | App Store Policy Compliance Agent |
| 3 | `uc3-genius-bar` | Retail Triage and Escalation Agent |
| 4 | `uc4-devrel` | Developer Relations Insights Agent |
| 5 | `uc5-hardware-failure` | Hardware Failure Pattern Detection Agent |

Each simulator provides **four streaming signal sources** and includes a **seeded anomaly** that activates after a configurable delay. Participant agents must detect the anomaly autonomously.

---

## Installation

Python 3.11+ required. Install the shared core first, then the specific use case:

```bash
# Install shared core
pip install -e common/techcompany-sim-core

# Install a use case simulator (example: UC1)
pip install -e uc1-supply-chain/techcompany-sim
```

---

## Running a Simulator

```bash
# Start the simulator (default port 8000)
sim-uc1 --port 8001

# Common options
sim-uc1 --port 8001 \
        --anomaly-delay 120 \
        --anomaly-intensity moderate \
        --seed 42
```

Once running, visit `http://localhost:8001/docs` for the interactive API reference.

### Anomaly Intensity Levels

| Level | Description |
|-------|-------------|
| `subtle` | Signals are ambiguous — for advanced teams |
| `moderate` | Clear pattern emerges across sources (default) |
| `obvious` | Unmistakable signal — good for demos |

---

## API Endpoints

Each simulator exposes the same endpoint pattern per signal source:

| Endpoint | Description |
|----------|-------------|
| `GET /<source>/events?since=<ts>&limit=100` | Poll for new events since a Unix timestamp |
| `GET /<source>/events/latest?limit=50` | Most recent N events |
| `GET /<source>/events/stream` | Server-Sent Events (SSE) push stream |
| `GET /health` | Server health and available sources |
| `GET /anomaly/status` | Anomaly state across all sources |
| `GET /<source>/status` | Per-source stats |

**Recommended polling pattern for agents:** store the timestamp of the last received event and pass it as `?since=` on each cycle.

---

## Generating Static Seed Data

Generate JSON snapshots for offline development:

```bash
sim-generate-uc1 --output ./seed-data/ --duration 600
```

---

## Kubernetes Deployment

Each use case includes a manifest in `<uc-folder>/techcompany-sim/k8s/simulator.yaml`.

```bash
# Build and push image
docker build -t <ecr-repo>/techcompany-sim-uc1:latest uc1-supply-chain/techcompany-sim/
docker push <ecr-repo>/techcompany-sim-uc1:latest

# Deploy
kubectl apply -f uc1-supply-chain/techcompany-sim/k8s/simulator.yaml
```

Agents in the same cluster reach the simulator at:
```
http://techcompany-sim-uc1:8001/<source>/events
```

---

## Data Schemas

Each use case folder contains a `SCHEMA.md` with full field-level documentation for all four signal sources, including enumerated values, anomaly patterns, and example events.

---

## Development Notes

- The `is_anomaly` flag is present on every event — use it during development to verify detection logic, then remove it from agent prompts for the live demo.
- Use `--seed` for reproducible event sequences across runs.
- The common core in `common/techcompany-sim-core/` is the only shared dependency — each UC simulator otherwise has no knowledge of other use cases.
