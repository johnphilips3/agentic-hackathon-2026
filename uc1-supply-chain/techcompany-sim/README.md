# techcompany-sim-uc1

Hackathon data simulator for **UC1 — Supply Chain Disruption Response Agent**.

This simulator provides four continuously streaming signal source endpoints that agents can poll or subscribe to via SSE. The simulator includes a seeded anomaly that activates after a configurable delay.

---

## Installation

This simulator depends on the common `techcompany-sim-core` package. Install both:

```bash
# From the project root directory
pip install -e common/techcompany-sim-core
pip install -e uc1-supply-chain/techcompany-sim
```

Requires Python 3.11+.

---

## Usage

### Start the simulator

```bash
sim-uc1 --port 8001
```

### Common options

```
--port INTEGER                          HTTP port  [default: 8000]
--host TEXT                             Bind host  [default: 0.0.0.0]
--tick-interval FLOAT                   Seconds between event ticks  [default: 2.0]
--anomaly-delay FLOAT                   Seconds after startup before anomaly activates  [default: 120.0]
--anomaly-intensity [subtle|moderate|obvious]  [default: moderate]
--anomaly-duration FLOAT                Seconds each anomaly episode lasts (0 = permanent)  [default: 0.0]
--anomaly-cycle-interval FLOAT          Seconds between anomaly episodes when anomaly-duration > 0  [default: 0.0]
--seed INTEGER                          RNG seed for reproducible runs  [default: 42]
```

### Example with custom settings

```bash
sim-uc1 --port 8001 --anomaly-delay 60 --anomaly-intensity obvious
```

### Anomaly mode examples

```bash
# Default — anomaly fires after 60s and runs permanently (original behavior)
sim-uc1 --port 8001 --anomaly-delay 60

# Single window — anomaly fires after 60s, lasts 120s, then stops
sim-uc1 --port 8001 --anomaly-delay 60 --anomaly-duration 120

# Cycling — anomaly fires for 60s, recovers for 30s, repeats
sim-uc1 --port 8001 --anomaly-delay 30 --anomaly-duration 60 --anomaly-cycle-interval 30
```

---

## Signal Sources

| Endpoint | Description |
|----------|-------------|
| `/supplier-capacity/events` | Tier-1/2 supplier capacity and quality events |
| `/logistics/events` | Freight status, port congestion, delay events |
| `/geopolitical/events` | News events tagged by geography and SC relevance |
| `/inventory/events` | Component inventory snapshots by warehouse |

**Seeded Anomaly:** CoreFab International (APAC-East) suffers a cascading capacity collapse driven by an export restriction, triggering logistics congestion and revealing critically low cellular-modem inventory.

---

## API Endpoints

Once running, visit `http://localhost:8001/docs` for the interactive Swagger UI.

### Poll (recommended for agents)

```
GET /<source>/events?since=<unix_timestamp>&limit=100
```

Returns events with `timestamp > since`. Store the timestamp of the last received event and pass it as `since` on each poll cycle.

### Latest shortcut

```
GET /<source>/events/latest?limit=50
```

Returns the most recent N events without needing a timestamp.

### SSE stream (push)

```
GET /<source>/events/stream
```

Server-Sent Events stream. Each message is a JSON-encoded event.

### Meta endpoints

```
GET /health              — server health and available sources
GET /anomaly/status      — anomaly state and delay for all sources
GET /<source>/status     — per-source stats and configuration
```

---

## Generating Static Seed Data

Generate JSON snapshots for offline development:

```bash
sim-generate-uc1 --output ./seed-data/
```

### Options

```
--duration FLOAT                        Simulated duration in seconds  [default: 600.0]
--tick-interval FLOAT                   Seconds between ticks  [default: 2.0]
--anomaly-delay FLOAT                   Seconds before anomaly activates (default: half duration)
--anomaly-intensity [subtle|moderate|obvious]  [default: moderate]
--anomaly-duration FLOAT                Seconds each anomaly episode lasts (0 = permanent)  [default: 0.0]
--anomaly-cycle-interval FLOAT          Seconds between anomaly episodes when anomaly-duration > 0  [default: 0.0]
--seed INTEGER                          RNG seed  [default: 42]
--output TEXT                           Output directory  [default: ./seed-data]
```

---

## Running in Kubernetes

Build and push the image:

```bash
docker build -t <ecr-repo>/techcompany-sim-uc1:latest .
docker push <ecr-repo>/techcompany-sim-uc1:latest
```

Deploy with the provided manifest:

```bash
# Update k8s/simulator.yaml with your ECR repository URI
kubectl apply -f k8s/simulator.yaml
kubectl get svc -n techcompany-sim
```

Agents running in the same cluster reach the simulator via:

```
http://techcompany-sim-uc1:8001/<source>/events
```

---

## Tips

- Poll at 2-5 second intervals. The default tick is 2s.
- Use `?since=<timestamp>` on every poll to only get new events.
- Check `/anomaly/status` to confirm the anomaly is active before your demo.
- The `is_anomaly` flag is visible — use it to verify your detection logic, then remove it from prompts for the live demo.
- Run with `--anomaly-intensity subtle` during development, switch to `moderate` or `obvious` for live demos.
- Use `--anomaly-duration` and `--anomaly-cycle-interval` to run repeating anomaly cycles. Omitting both preserves the original permanent latch behavior.

---

## Reproducibility

Use `--seed` to get identical event sequences:

```bash
sim-uc1 --seed 1337 --anomaly-delay 60
```
