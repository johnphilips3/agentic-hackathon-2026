# techcompany-sim-uc2

Hackathon data simulator for **UC2 — App Store Policy Compliance Agent**.

This simulator provides four continuously streaming signal source endpoints that agents can poll or subscribe to via SSE. The simulator includes a seeded anomaly that activates after a configurable delay.

---

## Installation

This simulator depends on the common `techcompany-sim-core` package. Install both:

```bash
# From the project root directory
pip install -e common/techcompany-sim-core
pip install -e uc2-app-store/techcompany-sim
```

Requires Python 3.11+.

---

## Usage

### Start the simulator

```bash
sim-uc2 --port 8002
```

### Common options

```
--port INTEGER                HTTP port  [default: 8000]
--host TEXT                   Bind host  [default: 0.0.0.0]
--tick-interval FLOAT         Seconds between event ticks  [default: 2.0]
--anomaly-delay FLOAT         Seconds after startup before anomaly activates [default: 120.0]
--anomaly-intensity [subtle|moderate|obvious]  [default: moderate]
--seed INTEGER                RNG seed for reproducible runs  [default: 42]
```

### Example with custom settings

```bash
sim-uc2 --port 8002 --anomaly-delay 60 --anomaly-intensity obvious
```

---

## Signal Sources

| Endpoint | Description |
|----------|-------------|
| `/submission-queue/events` | Incoming app submissions and version updates |
| `/policy-kb/events` | Policy knowledge base query activity |
| `/submission-history/events` | Prior review outcomes by bundle ID |
| `/escalation-queue/events` | Human-flagged cases awaiting AI recommendation |

**Seeded Anomaly:** Developer account dev_account_7741 submits progressive updates to com.obscure.tracker that increasingly obscure data collection practices — from incomplete manifests to zero declared data types.

---

## API Endpoints

Once running, visit `http://localhost:8002/docs` for the interactive Swagger UI.

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
sim-generate-uc2 --output ./seed-data/
```

### Options

```
--duration FLOAT              Simulated duration in seconds  [default: 600.0]
--tick-interval FLOAT         Seconds between ticks  [default: 2.0]
--anomaly-delay FLOAT         Seconds before anomaly activates (default: half duration)
--anomaly-intensity [subtle|moderate|obvious]  [default: moderate]
--seed INTEGER                RNG seed  [default: 42]
--output TEXT                 Output directory  [default: ./seed-data]
```

---

## Running in Kubernetes

Build and push the image:

```bash
docker build -t <ecr-repo>/techcompany-sim-uc2:latest .
docker push <ecr-repo>/techcompany-sim-uc2:latest
```

Deploy with the provided manifest:

```bash
# Update k8s/simulator.yaml with your ECR repository URI
kubectl apply -f k8s/simulator.yaml
kubectl get svc -n techcompany-sim
```

Agents running in the same cluster reach the simulator via:

```
http://techcompany-sim-uc2:8002/<source>/events
```

---

## Tips

- Poll at 2-5 second intervals. The default tick is 2s.
- Use `?since=<timestamp>` on every poll to only get new events.
- Check `/anomaly/status` to confirm the anomaly is active before your demo.
- The `is_anomaly` flag is visible — use it to verify your detection logic, then remove it from prompts for the live demo.
- Run with `--anomaly-intensity subtle` during development, switch to `moderate` or `obvious` for live demos.

---

## Reproducibility

Use `--seed` to get identical event sequences:

```bash
sim-uc2 --seed 1337 --anomaly-delay 60
```
