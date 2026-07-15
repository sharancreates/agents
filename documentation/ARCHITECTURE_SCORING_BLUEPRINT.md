# Technical Blueprint: Prompt Engineering for Architecture Scoring

This blueprint outlines the prompt engineering strategy, context structure, and scoring rubric implemented on Day 11 of the Originality Agent engineering sprint to evaluate repository architecture using Claude.

---

## 1. System Prompt Engineering Layout

The system prompt is structured to enforce a strict analytical persona and a machine-readable JSON output format:

*   **Persona Definition**: Sets the role as a *Senior Systems Architecture Evaluator*, establishing technical authority and detail expectations.
*   **Evaluation Mandates**: Directs Claude to analyze design patterns, detect manifest mismatches, and assess README authenticity.
*   **Response Schema Constraint**: Enforces a strict JSON response. No markdown chat text is allowed before or after the JSON block, enabling programmatic parsing via standard `json.loads()`.

---

## 2. Systemic Context Structure

To assess structural originality, the evaluator constructs a comprehensive context payload of the repository:

1.  **Directory Hierarchies**: Generates an ASCII representation using a depth-first traversal of the repository directory tree (excluding paths specified in `.gitignore`). This reveals packaging habits, separation of concerns, and component modules.
2.  **Dependency Manifests**: Extracts the contents of package files (e.g. `requirements.txt`, `package.json`, `Cargo.toml`). This highlights the project's dependency footprints and ecosystem.
3.  **Project Documentation**: Reads the `README.md` structure. Claude uses this to verify if the documentation represents actual architectural design decisions or is copied boilerplate.

---

## 3. Structural Evaluation Rubric

Claude evaluates the repository across three primary criteria, rated from `0.0` to `1.0`:

### A. Design Integrity (0.0 to 1.0)
*   **Definition**: Evaluates the cleanliness and correctness of software patterns.
*   **Criteria**: Checks for circular dependencies, modular separation of layers, encapsulation of database code, and clear entrypoints.
*   **Score Impact**: High scores ($>0.85$) represent clean, decoupled design patterns (such as Onion, Hexagonal, or MVC architecture).

### B. Structural Novelty (0.0 to 1.0)
*   **Definition**: Evaluates whether the layout is custom-designed or follows generic online tutorials.
*   **Criteria**: Detects common structure configurations typical of student project templates or cloned repositories.
*   **Score Impact**: Lower scores indicate standard, unaltered tutorial structures.

### C. README Consistency (0.0 to 1.0)
*   **Definition**: Validates if the project description matches the code reality.
*   **Criteria**: Checks if mentioned modules, databases, or API routes are actually present in the directory tree.
*   **Score Impact**: Discrepancies drop the score below $0.50$, indicating a high probability that the code has been plagiarized or modified from another project without updating the documentation.

---

## 4. Implementation Location
*   Evaluation Module: [architecture_evaluator.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/architecture_evaluator.py)
