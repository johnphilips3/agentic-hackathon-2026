# UC2: App Store Policy Compliance Agent - Data Schemas

This document describes the data structure for each signal source in UC2. Use these schemas to understand the data your agent will receive from the simulator.

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


## UC2: App Store Policy Compliance Agent

### 1. submission-queue

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "bundle_id": "string",
  "developer_account": "string",
  "app_category": "Games" | "Productivity" | "Health & Fitness" | "Finance" | "Social Networking" | "Photo & Video" | "Education" | "Shopping" | "Entertainment" | "Business" | "Utilities",
  "platform": "iOS" | "macOS" | "watchOS" | "tvOS" | "visionOS",
  "version": "string",
  "declared_capabilities": ["string"],
  "privacy_manifest_complete": boolean,
  "data_types_declared": ["usage-data" | "contact-info" | "location" | "identifiers" | "purchases" | "diagnostics"],
  "iap_configured": boolean,
  "content_rating": "4+" | "9+" | "12+" | "17+",
  "geographic_availability": ["string"],
  "submission_type": "new" | "update",
  "review_notes": string | null
}
```

**Example:**
```json
{
  "bundle_id": "com.obscure.tracker",
  "developer_account": "dev_account_7741",
  "app_category": "Social Networking",
  "platform": "iOS",
  "version": "4.0.0",
  "declared_capabilities": ["location-always", "tracking", "contacts", "camera", "microphone"],
  "privacy_manifest_complete": false,
  "data_types_declared": [],
  "iap_configured": false,
  "content_rating": "4+",
  "geographic_availability": ["US", "EU", "UK", "DE", "JP", "AU", "IN", "BR"],
  "submission_type": "update",
  "review_notes": "Bug fixes"
}
```

### 2. policy-kb

**Tick Rate:** Every 2 ticks (default: 4s)

**Schema:**
```json
{
  "query_type": "rule-lookup" | "precedent-search" | "jurisdiction-check",
  "policy_section": "string",
  "jurisdiction": "US" | "EU" | "UK" | "DE" | "JP" | "AU" | "IN" | "BR",
  "result_count": int,
  "confidence": float (0.0-1.0),
  "triggered_by": "string (bundle_id)"
}
```

**Example:**
```json
{
  "query_type": "rule-lookup",
  "policy_section": "5.1.1 Data Collection and Storage",
  "jurisdiction": "EU",
  "result_count": 6,
  "confidence": 0.91,
  "triggered_by": "com.obscure.tracker"
}
```

### 3. submission-history

**Tick Rate:** Every 3 ticks (default: 6s)

**Schema:**
```json
{
  "bundle_id": "string",
  "developer_account": "string",
  "review_date": "string (YYYY-MM-DD)",
  "outcome": "approved" | "rejected" | "warned" | "revision-requested",
  "violation_section": string | null,
  "remediation_taken": boolean | null,
  "resubmission_count": int
}
```

**Example:**
```json
{
  "bundle_id": "com.obscure.tracker",
  "developer_account": "dev_account_7741",
  "review_date": "2024-09-15",
  "outcome": "rejected",
  "violation_section": "5.1.1 Data Collection and Storage",
  "remediation_taken": false,
  "resubmission_count": 6
}
```

### 4. escalation-queue

**Tick Rate:** Every 4 ticks (default: 8s)

**Schema:**
```json
{
  "bundle_id": "string",
  "escalation_reason": "string",
  "reviewer_confidence": float (0.0-1.0),
  "policy_sections_cited": ["string"],
  "recommended_disposition": string | null,
  "urgency": "low" | "medium" | "high"
}
```

**Example:**
```json
{
  "bundle_id": "com.obscure.tracker",
  "escalation_reason": "prior violation pattern — repeated underdeclaration of data types",
  "reviewer_confidence": 0.38,
  "policy_sections_cited": ["5.1.1 Data Collection and Storage", "5.1.2 Data Use and Sharing"],
  "recommended_disposition": null,
  "urgency": "high"
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
