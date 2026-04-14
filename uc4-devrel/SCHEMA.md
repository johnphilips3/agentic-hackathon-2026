# UC4: Developer Relations Insights Agent - Data Schemas

This document describes the data structure for each signal source in UC4. Use these schemas to understand the data your agent will receive from the simulator.

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


## UC4: Developer Relations Insights Agent

### 1. forum-feed

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "post_id": "string",
  "framework": "string",
  "platform": "iOS" | "macOS" | "watchOS" | "tvOS" | "visionOS",
  "sdk_version": "string",
  "post_type": "question" | "bug-report" | "feature-request" | "complaint" | "discussion",
  "sentiment": "positive" | "neutral" | "negative" | "very-negative",
  "title": "string",
  "view_count": int,
  "reply_count": int,
  "helpful_votes": int,
  "resolved": boolean
}
```

**Example:**
```json
{
  "post_id": "POST-482019",
  "framework": "VisionKit",
  "platform": "visionOS",
  "sdk_version": "4.2",
  "post_type": "bug-report",
  "sentiment": "very-negative",
  "title": "CRITICAL: VisionKit 4.2 crash rate spike in production — spatial audio APIs broken",
  "view_count": 8420,
  "reply_count": 94,
  "helpful_votes": 128,
  "resolved": false
}
```

### 2. appstore-connect

**Tick Rate:** Every tick (default: 2s)

**Schema:**
```json
{
  "feedback_id": "string",
  "feedback_type": "rejection-appeal" | "crash-report" | "iap-issue" | "metadata-question" | "testflight-issue",
  "app_category": "string",
  "platform": "string",
  "framework_cited": "string",
  "sdk_version": "string",
  "install_tier": "indie" | "mid-market" | "enterprise",
  "device_model": "string",
  "os_version": "string",
  "crash_rate_pct": float,
  "urgency": "low" | "medium" | "high"
}
```

**Example:**
```json
{
  "feedback_id": "ASC-72819",
  "feedback_type": "crash-report",
  "app_category": "AR/VR",
  "platform": "visionOS",
  "framework_cited": "VisionKit",
  "sdk_version": "4.2",
  "install_tier": "enterprise",
  "device_model": "Vision Pro",
  "os_version": "visionOS 1.2",
  "crash_rate_pct": 12.4,
  "urgency": "high"
}
```

### 3. crash-trends

**Tick Rate:** Every 3 ticks (default: 6s)

**Schema:**
```json
{
  "framework": "string",
  "sdk_version": "string",
  "platform": "string",
  "crash_rate_pct": float,
  "week_over_week_delta": float,
  "affected_app_count": int,
  "top_crash_signature": "string",
  "os_version_breakout": {
    "string": float
  }
}
```

**Example:**
```json
{
  "framework": "VisionKit",
  "sdk_version": "4.2",
  "platform": "visionOS",
  "crash_rate_pct": 15.8,
  "week_over_week_delta": 4.2,
  "affected_app_count": 1840,
  "top_crash_signature": "VisionKit.SpatialAudioSession.init::443",
  "os_version_breakout": {
    "visionOS 1.2": 15.8
  }
}
```

### 4. wwdc-engagement

**Tick Rate:** Every 4 ticks (default: 8s)

**Schema:**
```json
{
  "session_title": "string",
  "view_count": int,
  "completion_rate": float (0.0-1.0),
  "doc_traffic_delta": float,
  "sample_code_downloads": int,
  "related_forum_posts": int,
  "platform": "string"
}
```

**Example:**
```json
{
  "session_title": "Introducing VisionKit 4.2",
  "view_count": 24500,
  "completion_rate": 0.12,
  "doc_traffic_delta": 2.4,
  "sample_code_downloads": 180,
  "related_forum_posts": 320,
  "platform": "visionOS"
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
