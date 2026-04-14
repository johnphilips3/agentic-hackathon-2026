# UC1: Supply Chain Disruption Response Agent - Data Schemas

This document describes the data structure for each signal source in UC1. Use these schemas to understand the data your agent will receive from the simulator.

---

## Common Event Wrapper

All events are wrapped in a standard envelope:

```json
{
  "id": "uuid-string",
  "source": "source-name",
  "timestamp": 1715000000.0,
  "data": { /* source-specific payload */ },
  "is_anomaly": false
}
```

**Fields:**
- `id` (string): Unique event identifier (UUID v4)
- `source` (string): Signal source name (e.g., "supplier-capacity", "applecare-cases")
- `timestamp` (float): Unix timestamp (seconds since epoch)
- `data` (object): Source-specific event data (schemas below)
- `is_anomaly` (boolean): Whether this event was generated during the anomaly window


## UC1: Supply Chain Disruption Response Agent

### 1. supplier-capacity

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "supplier": "string",
  "tier": 1 | 2,
  "geography": "US-West" | "US-East" | "EU-West" | "EU-Central" | "APAC-East" | "APAC-South" | "LATAM" | "MEA",
  "component_type": "battery" | "display" | "camera-module" | "haptic-engine" | "cellular-modem" | "wifi-chip" | "touch-controller" | "power-management-ic" | "speaker-assembly" | "face-id-module",
  "event_type": "planned-downtime" | "quality-hold" | "workforce-reduction" | "capacity-expansion" | "shift-change" | "equipment-maintenance",
  "capacity_pct": float,
  "quality_yield_pct": float,
  "workforce_available_pct": float,
  "notes": string | null
}
```

**Example:**
```json
{
  "supplier": "CoreFab International",
  "tier": 1,
  "geography": "APAC-East",
  "component_type": "cellular-modem",
  "event_type": "quality-hold",
  "capacity_pct": 28.3,
  "quality_yield_pct": 82.45,
  "workforce_available_pct": 48.2,
  "notes": "EXPORT RESTRICTION IMPACT — production severely constrained"
}
```

### 2. logistics

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "carrier": "string",
  "mode": "air" | "ocean" | "ground",
  "origin": "string (geography)",
  "destination": "string (geography)",
  "component_type": "string",
  "status": "on-time" | "delayed" | "arrived" | "departed",
  "delay_hours": int,
  "delay_cause": "port-congestion" | "customs-hold" | "weather" | "carrier-capacity" | "none",
  "port_congestion_index": float (0.0-1.0)
}
```

**Example:**
```json
{
  "carrier": "OceanLink",
  "mode": "ocean",
  "origin": "APAC-East",
  "destination": "US-West",
  "component_type": "cellular-modem",
  "status": "delayed",
  "delay_hours": 168,
  "delay_cause": "port-congestion",
  "port_congestion_index": 0.82
}
```

### 3. geopolitical

**Tick Rate:** Every 3 ticks (default: 6s)

**Schema:**
```json
{
  "headline": "string",
  "geography": "string",
  "event_type": "export-control" | "labor-unrest" | "natural-disaster" | "regulatory-change" | "political-transition" | "trade-dispute",
  "severity": "low" | "medium" | "high" | "critical",
  "sc_relevance": "semiconductor" | "raw-materials" | "logistics" | "energy" | "labor",
  "confidence": float (0.0-1.0),
  "source": "Reuters Synthesis" | "Trade Monitor" | "Risk Pulse" | "Geo Intel Feed"
}
```

**Example:**
```json
{
  "headline": "APAC-East government imposes emergency semiconductor export restrictions targeting advanced modem components",
  "geography": "APAC-East",
  "event_type": "export-control",
  "severity": "critical",
  "sc_relevance": "semiconductor",
  "confidence": 0.94,
  "source": "Trade Monitor"
}
```

### 4. inventory

**Tick Rate:** Every 2 ticks (default: 4s)

**Schema:**
```json
{
  "component_type": "string",
  "warehouse": "SJC-1" | "AMS-2" | "SHA-3" | "DFW-4" | "LHR-5",
  "units_on_hand": int,
  "days_of_supply": float,
  "reorder_point": int,
  "in_transit_units": int,
  "alert": string | null
}
```

**Example:**
```json
{
  "component_type": "cellular-modem",
  "warehouse": "SJC-1",
  "units_on_hand": 3200,
  "days_of_supply": 4.2,
  "reorder_point": 45000,
  "in_transit_units": 0,
  "alert": "CRITICAL: 4.2 days of supply remaining — replenishment pipeline disrupted"
}
```

---

## Notes on Data Types

**Enumerations:** Fields listed with `|` separators indicate fixed enumeration values. Your agent should expect only these values.

**Nullable Fields:** Fields marked with `| null` may contain `null` values in certain conditions (typically when a field is not applicable).

**Float Ranges:** Percentage and index values are typically between 0.0 and 1.0 (or 0-100 for percentages). Sentiment scores range from -1.0 (very negative) to 1.0 (very positive).

**Timestamps:** All timestamps use Unix epoch format (seconds since 1970-01-01 00:00:00 UTC) as floating-point numbers.

**Tick Rates:** Some sources emit events less frequently than others. The tick rate indicates how many ticks must pass before a new event is generated. For example, "tick_rate=2" means events are emitted every 2 ticks.

---

## Anomaly Detection Hints

**The `is_anomaly` flag:** Every event includes an `is_anomaly` boolean field. This is `true` when the event was generated during the anomaly window. Use this flag during development to verify your detection logic, but remove it from your agent's decision-making before the live demo.

**Pattern Correlation:** The seeded anomaly manifests across **multiple signal sources simultaneously**. Your agent should correlate signals to identify the pattern:

- **UC1:** Watch for CoreFab International (APAC-East, cellular-modem) + logistics delays + export restrictions + inventory alerts
- **UC2:** Look for dev_account_7741 / com.obscure.tracker across submission queue + history + escalations
- **UC3:** Track serial prefix J7Q (Handset Pro 15) with haptic-engine failures + recurring repairs + parts depletion
- **UC4:** Correlate VisionKit 4.2 + visionOS across forum posts + crash reports + WWDC engagement drops
- **UC5:** Connect Handset Pro 15 Max lot K9R + CAM-117 + goodwill approvals + negative camera sentiment

**Intensity Levels:** The simulator runs with three intensity settings:
- **Subtle:** Anomaly is present but easy to miss without careful analysis
- **Moderate:** Clear pattern emerges with basic correlation (default for demos)
- **Obvious:** Unmistakable signal with high confidence scores

---

## API Consumption Patterns

**Poll Endpoint (Recommended):**
```
GET /<source>/events?since=<unix_timestamp>&limit=100
```

Store the `timestamp` of the last received event and pass it as `since` on each poll cycle (every 2-5 seconds).

**Latest Endpoint (Simpler):**
```
GET /<source>/events/latest?limit=50
```

Returns the most recent N events without needing timestamp tracking.

**SSE Stream (Push):**
```
GET /<source>/events/stream
```

Server-Sent Events stream. Events arrive as they're generated.

**Status Endpoints:**
```
GET /health                    # Overall simulator status
GET /anomaly/status            # Anomaly state across all sources
GET /<source>/status           # Per-source stats
```

---


## Example Workflow

1. **Startup:** Connect to simulator endpoints, initialize timestamp tracking
2. **Polling Loop:** Every 2-5 seconds, poll each source with `?since=<last_timestamp>`
3. **Processing:** Extract events, store in agent memory/database
4. **Analysis:** Run your reasoning loop to detect patterns across sources
5. **Detection:** When anomaly pattern detected, generate structured insight report
6. **Verification:** Check `/anomaly/status` to confirm the anomaly window is active

---

## Questions?

Refer to the simulator README and API documentation. Office hours are available during the hackathon for technical questions.

Good luck building your agent!
