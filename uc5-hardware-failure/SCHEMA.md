# UC5: Hardware Failure Pattern Detection and Field Action Agent - Data Schemas

This document describes the data structure for each signal source in UC5. Use these schemas to understand the data your agent will receive from the simulator.

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


## UC5: Hardware Failure Pattern Detection and Field Action Agent

### 1. applecare-cases

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "case_id": "string",
  "device_model": "string",
  "serial_prefix": "string",
  "firmware_version": "string",
  "geography": "string",
  "symptom_code": "string",
  "symptom_category": "string",
  "technician_notes": "string",
  "case_type": "phone" | "chat" | "in-store" | "mail-in",
  "resolution": "resolved" | "escalated" | "pending"
}
```

**Example:**
```json
{
  "case_id": "CS-2566777",
  "device_model": "Handset Pro 15 Max",
  "serial_prefix": "K9R",
  "firmware_version": "17.5.0",
  "geography": "APAC-East",
  "symptom_code": "CAM-117",
  "symptom_category": "CAM",
  "technician_notes": "Camera module failure confirmed (CAM-117). Rear camera array non-functional. Lot prefix K9R. Component replaced.",
  "case_type": "in-store",
  "resolution": "escalated"
}
```

### 2. repair-depot

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "report_id": "string",
  "device_model": "string",
  "serial_prefix": "string",
  "component_failed": "string",
  "failure_code": "string",
  "repair_action": "component-replacement" | "board-level-repair" | "software-restore" | "cosmetic-repair" | "no-fault-found" | "express-replacement",
  "root_cause": "customer-damage" | "wear" | "manufacturing" | "software" | "unknown",
  "parts_consumed": int,
  "depot_location": "AUS-Austin" | "IRL-Cork" | "SGP-Jurong" | "CZE-Brno",
  "technician_grade": "L1" | "L2" | "L3"
}
```

**Example:**
```json
{
  "report_id": "DEP-48291",
  "device_model": "Handset Pro 15 Max",
  "serial_prefix": "K9R",
  "component_failed": "camera-module",
  "failure_code": "CAM-117",
  "repair_action": "component-replacement",
  "root_cause": "manufacturing",
  "parts_consumed": 1,
  "depot_location": "IRL-Cork",
  "technician_grade": "L3"
}
```

### 3. warranty-claims

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "claim_id": "string",
  "device_model": "string",
  "serial_prefix": "string",
  "claim_type": "in-warranty" | "out-of-warranty" | "accidental-damage" | "applecare-plus",
  "symptom_code": "string",
  "approved": boolean,
  "approval_reason": "policy" | "goodwill" | "standard" | null,
  "claim_value_usd": float,
  "geography": "string",
  "device_age_days": int
}
```

**Example:**
```json
{
  "claim_id": "WC-5382463",
  "device_model": "Handset Pro 15 Max",
  "serial_prefix": "K9R",
  "claim_type": "out-of-warranty",
  "symptom_code": "CAM-117",
  "approved": true,
  "approval_reason": "goodwill",
  "claim_value_usd": 439.88,
  "geography": "APAC-East",
  "device_age_days": 399
}
```

### 4. sentiment-feed

**Tick Rate:** Every 2 ticks (default: 4s)

**Schema:**
```json
{
  "signal_id": "string",
  "device_model": "string",
  "channel": "app-store-reviews" | "support-chat" | "social-listening" | "nps-survey",
  "theme": "battery" | "camera" | "display" | "performance" | "overheating" | "connectivity" | "software" | "build-quality" | "speaker",
  "sentiment_score": float (-1.0 to 1.0),
  "volume_index": float (0.0-1.0),
  "sample_text": "string",
  "geography": "string"
}
```

**Example:**
```json
{
  "signal_id": "SIG-697347",
  "device_model": "Handset Pro 15 Max",
  "channel": "support-chat",
  "theme": "camera",
  "sentiment_score": -0.82,
  "volume_index": 0.91,
  "sample_text": "This is a hardware problem not software — camera is toast",
  "geography": "US-West"
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
