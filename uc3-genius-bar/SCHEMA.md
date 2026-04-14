# UC3: Retail Genius Bar Triage and Escalation Agent - Data Schemas

This document describes the data structure for each signal source in UC3. Use these schemas to understand the data your agent will receive from the simulator.

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


## UC3: Retail Genius Bar Triage and Escalation Agent

### 1. appointment-queue

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "appointment_id": "string",
  "store": "string",
  "device_model": "string",
  "serial_prefix": "string",
  "serial_number": "string",
  "appointment_type": "hardware" | "software" | "accidental-damage" | "setup-support",
  "symptom_description": "string",
  "customer_description": "string",
  "slot_time": "string (ISO 8601)",
  "warranty_status": "in-warranty" | "out-of-warranty" | "applecare-plus"
}
```

**Example:**
```json
{
  "appointment_id": "APT-45823",
  "store": "SFO-Union-Square",
  "device_model": "Handset Pro 15",
  "serial_prefix": "J7Q",
  "serial_number": "J7Q482931",
  "appointment_type": "hardware",
  "symptom_description": "haptic-not-working",
  "customer_description": "Haptic feedback completely stopped working — phone feels dead",
  "slot_time": "2024-11-15T14:00:00",
  "warranty_status": "in-warranty"
}
```

### 2. device-diagnostics

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "serial_number": "string",
  "device_model": "string",
  "battery_health_pct": int,
  "battery_cycles": int,
  "crash_log_flags": int,
  "storage_health": "good" | "degraded",
  "last_diagnostic_pass": boolean,
  "flagged_components": ["string"],
  "os_version": "string"
}
```

**Example:**
```json
{
  "serial_number": "J7Q482931",
  "device_model": "Handset Pro 15",
  "battery_health_pct": 94,
  "battery_cycles": 82,
  "crash_log_flags": 18,
  "storage_health": "good",
  "last_diagnostic_pass": false,
  "flagged_components": ["haptic-engine"],
  "os_version": "17.5.1"
}
```

### 3. repair-history

**Tick Rate:** Every 2 ticks (default: 4s)

**Schema:**
```json
{
  "serial_number": "string",
  "device_model": "string",
  "repair_date": "string (YYYY-MM-DD)",
  "repair_type": "component-replacement" | "software-restore" | "board-level-repair" | "cosmetic-repair" | "express-replacement-issued",
  "component_replaced": string | null,
  "technician_notes": "string",
  "outcome": "resolved" | "unresolved" | "recurring",
  "store": "string",
  "days_since_repair": int
}
```

**Example:**
```json
{
  "serial_number": "J7Q482931",
  "device_model": "Handset Pro 15",
  "repair_date": "2024-09-10",
  "repair_type": "component-replacement",
  "component_replaced": "haptic-engine",
  "technician_notes": "Haptic engine replaced. Unit returned to customer. Failure recurred after 12 days.",
  "outcome": "recurring",
  "store": "SFO-Union-Square",
  "days_since_repair": 12
}
```

### 4. parts-scheduling

**Tick Rate:** Every 2 ticks (default: 4s)

**Schema:**
```json
{
  "component_type": "string",
  "device_model": "string",
  "store": "string",
  "units_on_hand": int,
  "estimated_restock_days": int | null,
  "available_slots": {
    "standard": int,
    "senior": int,
    "specialist": int
  },
  "recommended_service_path": "in-store-same-day" | "in-store-scheduled" | "depot-repair" | "express-replacement" | "software-only"
}
```

**Example:**
```json
{
  "component_type": "haptic-engine",
  "device_model": "Handset Pro 15",
  "store": "SFO-Union-Square",
  "units_on_hand": 0,
  "estimated_restock_days": null,
  "available_slots": {
    "standard": 2,
    "senior": 1,
    "specialist": 0
  },
  "recommended_service_path": "depot-repair"
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
