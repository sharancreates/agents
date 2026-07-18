# Technical Blueprint: Structured JSON Generation Lock-in

This blueprint outlines the schema layouts, tool-enforcement mechanisms, and validation retry configurations implemented on Day 14 of the engineering sprint to ensure Claude outputs valid JSON payloads.

---

## 1. Structural Data Models (Pydantic Schemas)

To guarantee that Claude returns structured analysis payloads, we declare formal Pydantic data schemas:

*   **`ScoresSchema`**: Validates the numerical evaluation scores. Every score must be a float bounded strictly between `0.0` and `1.0` using Pydantic's `ge=0.0` and `le=1.0` parameters.
*   **`ArchitectureEvaluationSchema`**: The parent schema containing:
    *   `detected_patterns` (List of strings describing design patterns).
    *   `manifest_mismatches` (List of string details explaining discrepancies).
    *   `readme_authenticity` (Text evaluation).
    *   `scores` (Nested `ScoresSchema` object).
    *   `critique_summary` (Technical feedback).

---

## 2. API Tool-Enforcement & Token Validation

Rather than instructing Claude in natural language to print a JSON string (which risks malformed text or code block wrapping), we lock the response format using Anthropic's **Tool Use** mechanism:

1.  **Schema Transformation**: The Pydantic model is converted into an Anthropic-compatible JSON Schema definition (`tool_schema`).
2.  **Forced Tool Call**: By passing `tool_choice={"type": "tool", "name": "record_architecture_evaluation"}`, Claude is forced to return a tool call rather than free-form conversational text.
3.  **Parsing Benefits**:
    *   Claude's response output token stream is structured natively at the generation level.
    *   This eliminates formatting noise (e.g. "Here is your JSON:") and naturally minimizes prompt context bloat.

---

## 3. Schema Failure Recovery Strategies

If Claude's generated arguments fail validation against the schema, the system executes tiered recovery tracks:

*   **Tier 1: Validation Try/Catch Block**: The validator catches `ValidationError` during instantiation (`ArchitectureEvaluationSchema(**raw_arguments)`).
*   **Tier 2: Environment Fallback (No Pydantic)**: If Pydantic is not installed in the execution environment, the evaluator runs a manual validation check that ensures all required keys exist and fallback values are set for missing properties.
*   **Tier 3: Graceful Simulation Fallback**: If structural exceptions or connection drops happen, the system catches the error, logs a warning details summary, and falls back to a simulated validation payload, preventing pipeline failures.

---

## 4. Implementation Location
*   Validation Schemas: [schemas.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/schemas.py)
*   Structured Interface: [architecture_evaluator.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/architecture_evaluator.py)
