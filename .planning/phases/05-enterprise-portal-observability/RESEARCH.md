# Phase 5: Research - Enterprise Portal & Real-Time Observability

## 1. Technical Architecture & Communication Patterns

### 1.1 Real-Time Streaming: Server-Sent Events (SSE) vs WebSockets
For unidirectional telemetry from backend to frontend (agent thoughts, stage transitions, evaluation completion):
- **Why SSE?**
  - Native browser support via standard `EventSource` API with automatic reconnection and keep-alive handling.
  - Operates over standard HTTP/1.1 and HTTP/2 without custom websocket upgrade handshakes or load-balancer proxy hassles.
  - Simple `Content-Type: text/event-stream` with line-delimited `data: {...}\n\n` formatting.
  - Clean fallback to periodic polling (`GET /v1/evaluations/{id}/traces`) if SSE stream terminates or client browser disconnects.

```
Frontend (EventSource)                       FastAPI (Starlette StreamingResponse)
         │                                                     │
         ├─────────── GET /v1/evaluations/{id}/stream ────────►│
         │                                                     │
         │◄────────── data: {"stage": "recon", ...}\n\n ───────┤
         │                                                     │
         │◄────────── data: {"stage": "qa_sandbox", ...}\n\n ──┤
         │                                                     │
         │◄────────── data: {"stage": "critic", ...}\n\n ──────┤
         │                                                     │
         │◄────────── data: {"stage": "complete", ...}\n\n ────┤
```

---

## 2. Developer Console & Multi-Tenant Portal

### 2.1 API Key Lifecycle Management
- **Key Display Invariant**: The full plaintext API key (`ak_live_{prefix}_{secret}`) is generated on the server and returned **only once** upon creation. The frontend displays a persistent modal with a one-click copy button and alert warning to store the secret.
- **Listing Active Keys**: Key listings display only the key prefix (`ak_live_a1b2c3d4...`), name, granted scopes, and last used timestamp.

### 2.2 Webhook Configuration & Health Check
- Allows partners to register HTTPS URLs to receive HMAC-SHA256 signed event payloads (`evaluation.completed`, `evaluation.failed`).
- Frontend provides an immediate "Send Test Webhook" action validating delivery status and latency.

### 2.3 Razorpay Credit Balance & Top-Up Modal
- Displays current credit balance and consumption ledger.
- Provides one-click purchase buttons for:
  - **Starter Pack**: ₹499 (100 credits)
  - **Pro Pack**: ₹1,999 (500 credits)
  - **Enterprise Pass**: ₹5,999 (2,000 credits)
- Integrates with `/v1/billing/orders` and `/v1/billing/verify-payment` for instant automated fulfillment.

---

## 3. Rubric Customization & Weight Mathematics

Rubric evaluation combines scores across four core dimensions:
$$\text{Overall Score} = \sum_{d \in D} \frac{w_d}{100} \cdot S_d$$
where $D = \{\text{code\_quality}, \text{functionality}, \text{originality}, \text{innovation}\}$ and:
$$\sum_{d \in D} w_d = 100.0$$

The frontend interactive rubric customizer enforces:
1. Sliders dynamically update dimension weights.
2. If total $\ne 100\%$, an alert highlights the discrepancy with a single-click "Auto-Normalize to 100%" action.
3. Custom challenge prompt text (e.g. "Focus strictly on security and input validation") is passed directly into evaluation requests.

---

## 4. Judge Copilot Integration
- Connects directly to `POST /v1/evaluations/{id}/chat` established in Phase 4.5.
- Displays streaming or formatted responses with clickable citation chips (`file_path:L12-L35`).
- Enables judges to verify ambiguous or contested implementations instantly.
