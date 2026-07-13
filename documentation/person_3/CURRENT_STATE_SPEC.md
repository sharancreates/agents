# 🗺️ Code Quality Agent: Complete 15-Day Engineering Specification

**Document Reference:** `documentation/person_2/CODE_QUALITY_ROADMAP.md`  
**Subsystem Owner:** Person 2 (Code Quality & Execution Agent)  
**System Class:** Static Analysis & Dynamic Runtime Execution Sandbox  
**Target Consumer:** Person 1 (Orchestration & Sandboxing), Person 3 (Originality/Embeddings), Person 4 (Reporting/Dashboard)

---

## 🎯 Executive Architectural Objective
The Code Quality Agent is an automated, secure, and multi-threaded evaluation engine designed to ingest raw student/participant source code across varying language frameworks. The engine evaluates incoming packages across two clear vectors:

1. **Static Metrics:** Syntax analysis, Abstract Syntax Tree (AST) micro-inspections, mathematical cyclomatic flow calculations, structural code-smell flagging, and production-grade ecosystem linting.
2. **Dynamic Operations:** Isolated runtime subprocess containment execution, runtime crash diagnostics, execution timeout guarantees, and automated unit test assertion scoring.

All extracted insights are formatted and mapped directly into strict Pydantic models to feed downstream reporting layers.

---

## 🛠️ Phase 1: Foundation & AST Parsing Core (Days 1–5)

### 📌 Day 1: Project Scaffolding & Language Identification
* **Technical Objective:** Establish the foundation of the workspace domain. Build an autonomous classification engine that reliably identifies file extensions and POSIX execution headers (shebang lines). This setup ensures the system knows exactly which compiler or parser to run before processing a file.
* **Algorithmic Blueprint:**
    * Implement an entry-point scanning matrix that handles two data inputs: the target file extension and the first line of the file byte stream (the shebang vector).
    * If a file ends with `.py`, or if its first line contains `#!/usr/bin/env python`, it is mapped to the Python execution profile.
    * If a file ends with `.js`, `.ts`, `.jsx`, or `.tsx`, it maps to the JavaScript/TypeScript execution matrix.
    * Fallback states revert to text profiles or flag an immediate structure error to prevent system hangs.
* **Component Deliverable:** `person_2/core/detector.py` via `LanguageDetector`.
* **Testing Gateway:** `test_detector.py` confirming shebang decoding, empty stream behaviors, and missing extension profiles.

---

### 📌 Day 2: Abstract Syntax Tree (AST) Complexity Analytics
* **Technical Objective:** Build an engine to parse raw code into a concrete tree and evaluate its underlying structural density using **Cyclomatic Complexity**. The system must count distinct, independent logical paths without using recursive functions that risk crashing the runtime under heavy nesting.
* **Algorithmic Blueprint:**
    * Initialize the parsing wrapper via a cross-platform compilation fallback engine. 
    * Instead of using deep recursive tree-walking functions that risk filling up the operating system call stack on complex codebases, implement an explicit queue-stack array (Depth-First Search loop iteration) to traverse tree blocks.
    * Count branching nodes based on the target language. For Python, it tracks: `if_statement`, `while_statement`, `for_statement`, `except_clause`, `conditional_expression` (ternary patterns), and `boolean_operator` blocks (`and`, `or`).
    * Compute the graph density score using the structural path baseline formula:
      $$\text{Complexity} = \text{Decision Branches} + 1$$
* **Component Deliverable:** `person_2/core/complexity.py` via `CyclomaticComplexityCalculator`.
* **Testing Gateway:** `test_complexity.py` asserting exact complexity balances for flat sequentials ($C=1$), simple branches ($C=2$), and stacked multi-conditional layers.

---

### 📌 Day 3: Subprocess Execution Layer for External Linters
* **Technical Objective:** Integrate production-grade static linters (`ruff` for Python, `eslint` for JavaScript) by spinning up isolated system subprocesses. This layer must capture error streams without causing the primary engine to deadlock or hang.
* **Algorithmic Blueprint:**
    * Avoid utilizing raw `subprocess.Popen` pipes without manual flushing routines, as overflowing internal OS buffers will cause the pipeline execution threads to freeze indefinitely.
    * Leverage `subprocess.run` with explicitly mapped `capture_output=True` and `text=True` execution arguments. This setup ensures output text is flushed directly into secure RAM vectors.
    * Append precise CLI array flags to guarantee deterministic JSON output streams:
        * Python: `["ruff", "check", file_path, "--output-format", "json"]`
        * JavaScript: `["npx", "eslint", file_path, "--format", "json"]`
    * Implement a data translation interface that normalizes linter outputs into a unified dictionary structure containing: `rule`, `message`, `line`, `column`, and `severity`.
* **Component Deliverable:** `person_2/core/linters.py` via `LinterExecutionEngine`.
* **Testing Gateway:** `test_linters.py` verifying JSON extraction capabilities using mocked `subprocess.run` data streams.

---

### 📌 Day 4: Structural Code Smell Identification
* **Technical Objective:** Go beyond simple linter rules by analyzing the AST tree to flag high-level structural design flaws (code smells), specifically targeting **Long Functions** and **Deep Nesting**.
* **Algorithmic Blueprint:**
    * **Long Functions Rule:** Traverse the syntax tree and isolate function definition blocks. Extract their structural line-coordinate metadata (`start_point` and `end_point`). Calculate the absolute size delta:
      $$\text{Delta} = \text{End Row} - \text{Start Row} + 1$$
      Flag any functions exceeding the defined threshold (e.g., 20 lines) as an architectural warning.
    * **Deep Nesting Rule:** Walk the AST while maintaining a tracking state of the current structural depth. When entering code-block structures (`if_statement`, `for_statement`, `while_statement`, `try_statement`), increment the depth tracking counter. If the score exceeds the defined safety threshold (e.g., depth > 3), flag a nesting violation at the exact offending line coordinate.
* **Component Deliverable:** `person_2/core/rules.py` via `CodeSmellDetector`.
* **Testing Gateway:** `test_rules.py` validating nested node layouts and function block size detections.

---

### 📌 Day 5: Metrics Aggregation & Schema Standardization
* **Technical Objective:** Synthesize static linter findings, structural code smells, and cyclomatic complexity scores into a unified scoring framework. Map these aggregated metrics onto a strict, centralized Pydantic data model to maintain schema compliance across the entire team.
* **Algorithmic Blueprint:**
    * Build an orchestration wrapper that ingests a target directory and coordinates execution across all foundations built during Days 1–4.
    * Aggregate linter issue counts and code smell weightings into a normalized structural score deduction scale (starting from a baseline score of 100).
    * Map the completed payload directly to the group's centralized schema definitions:
        * Isolate code maintainability ratings into high, medium, and critical risk flags based on whether the cyclomatic complexity index spans above 10 or 15 points.
        * Structure the data to match the primary `EvaluationResult` specification shared with Person 1 and Person 4.
* **Component Deliverable:** `person_2/models/schemas.py` and an automated metrics assembly worker.
* **Testing Gateway:** Validate total metric collection schemas and ensure they pass strict Pydantic type constraints under edge-case inputs.

---

## 🚀 Phase 2: Dynamic Execution & Sandboxing (Days 6–10)

### 📌 Day 6: Subprocess Code Runner Engine
* **Technical Objective:** Transition from static code analysis to dynamic execution. Design a code runner core that securely spawns local code threads to run student code submissions across multiple language environments.
* **Algorithmic Blueprint:**
    * Interface directly with Person 1's orchestration layers to receive unzipped workspace directories.
    * Construct separate execution environment run profiles based on the language profile discovered on Day 1:
        * Python Profile: Run using the host system's explicit Python binary loop path layout `[sys.executable, file_path]`.
        * Node.js Profile: Run via the local executable system runtime path wrapper `["node", file_path]`.
    * Isolate standard input streams (`stdin`) to allow code files with interactive prompts to accept pre-defined test inputs without hanging the terminal.
* **Component Deliverable:** `person_2/core/runner.py` via `DynamicCodeRunner`.
* **Testing Gateway:** Run short execution scripts and confirm stdout is captured cleanly.

---

### 📌 Day 7: Resource Limitation & Timeout Enforcer
* **Technical Objective:** Secure the environment against malicious code or accidental infinite loops. Implement a hard execution timeout layer to kill hanging processes before they exhaust host system resources.
* **Algorithmic Blueprint:**
    * Establish an immutable timeout threshold (e.g., 5.0 seconds maximum per script execution run).
    * Implement the constraint architecture natively inside the `subprocess.run` window via the `timeout` parameter.
    * Catch the resulting `subprocess.TimeoutExpired` exception explicitly. When triggered, the system must forcefully terminate the underlying process ID tree, clean up hanging system processes, and gracefully return a structured error report to prevent cascade failures in the main loop.
* **Component Deliverable:** Process tracking interceptors inside `DynamicCodeRunner`.
* **Testing Gateway:** Execute a script containing a terminal loop `while True: pass` and verify that the engine forcefully terminates it within the exact millisecond threshold.

---

### 📌 Day 8: Unit Test Harness Orchestrator
* **Technical Objective:** Build an internal test execution coordinator that maps input unit test datasets onto student submissions and manages automated verification passes.
* **Algorithmic Blueprint:**
    * Design a test harness layer capable of mapping evaluation test cases to code submissions in two ways:
        1. **Functional Mapping:** Passing structured data arguments directly into specific function targets.
        2. **IO-Bound Mapping:** Injecting custom input strings into `stdin` and capturing the corresponding outputs on `stdout`.
    * Loop through test manifests sequentially, feeding parameters dynamically into the code runner core built on Day 6.
* **Component Deliverable:** `person_2/core/harness.py` via `UnitTestOrchestrator`.
* **Testing Gateway:** Run an evaluation manifest against a basic math script and verify that multiple test passes are tracked accurately.

---

### 📌 Day 9: Assertion Parser & Pass-Rate Aggregator
* **Technical Objective:** Parse the output streams from the execution run, cross-reference them with the target test answers, and calculate the overall test pass rate.
* **Algorithmic Blueprint:**
    * Implement a clean text-processing pipeline that strips hidden white spaces, carriage returns (`\r\n`), and terminal trailing breaks from both captured outputs and expected answers.
    * Evaluate equality matches or structural substring containment assertions.
    * Compute the absolute pass-rate percentage using the standard performance equation:
      $$\text{Pass Rate} = \left( \frac{\text{Passed Assertions}}{\text{Total Assertions}} \right) \times 100$$
* **Component Deliverable:** Scoring logic layers within `UnitTestOrchestrator`.
* **Testing Gateway:** Confirm correct scoring outputs when evaluations return mixed results (e.g., partial passes like 2/3 correct).

---

### 📌 Day 10: Runtime Crash Exception Diagnostics
* **Technical Objective:** Capture runtime crashes (e.g., `ZeroDivisionError`, `TypeError`, `ReferenceError`), parse the stack traces, and extract the root cause into a clear, human-readable error summary.
* **Algorithmic Blueprint:**
    * Intercept standard error output streams (`stderr`) whenever an execution runner exits with a non-zero system return code.
    * Use regular expression pattern matching to extract the file path, line number, and error type from stack traces:
        * Python Regex Target: `r"File \"(.*)\", line (\d+), in (.*)\n(?:.*\n){0,1}(.*): (.*)"`
        * JavaScript Trace Target: Isolate error messages containing `at Object.<anonymous>` patterns.
    * Package these diagnostics into a readable format for the dashboard layer managed by Person 4.
* **Component Deliverable:** `person_2/core/diagnostics.py` via `RuntimeExceptionClassifier`.
* **Testing Gateway:** Intentionally execute code designed to throw a `ZeroDivisionError` and assert that the parser accurately extracts line coordinates and crash reasons.

---

## 📈 Phase 3: Enterprise Hardening & Integration (Days 11–15)

### 📌 Day 11: Cross-Platform File Paths & Memory Caching
* **Technical Objective:** Normalize all file paths so the engine runs seamlessly on Windows local environments and Linux production sandboxes. Implement caching for frequently accessed configuration files to reduce disk IO overhead.
* **Algorithmic Blueprint:**
    * Audit every file system interaction and replace string-based path concatenations with explicit `os.path` operations or pure `pathlib.Path` structures. This eliminates path separator conflicts (`/` vs `\`) between Windows and Linux.
    * Implement a simple memory cache wrapper around linter rulesets and configuration files to save processing cycles during bulk test evaluations.
* **Component Deliverable:** `person_2/utils/paths.py` path-normalization utilities.
* **Testing Gateway:** Run test passes across differing drive path formats to ensure cross-platform compatibility.

---

### 📌 Day 12: Shared Mocking Framework for Peer Integration
* **Technical Objective:** Build an integration gateway that allows Person 1's main orchestration loop to cleanly invoke your code quality evaluation features.
* **Algorithmic Blueprint:**
    * Expose a unified class entry point `CodeQualityAgentFacade` that simplifies the entire underlying subsystem into a single function call:
      `def evaluate_submission(directory_path: str, tests_manifest: dict) -> EvaluationResult:`
    * Provide lightweight, predictable mock interfaces for your modules. This allows your team members to continue developing their orchestration loops and data pipelines without needing your full system modules locally active.
* **Component Deliverable:** `person_2/integration/facade.py`.
* **Testing Gateway:** Ensure the facade can be imported and executed with mock payloads without triggering side effects.

---

### 📌 Day 13: Bulk Performance & Memory Profiling
* **Technical Objective:** Monitor and record performance metrics—such as execution time and peak memory footprint—for each code evaluation pass.
* **Algorithmic Blueprint:**
    * Wrap execution loops with high-resolution monotonic CPU timers (`time.monotonic()`) to track exact execution duration down to the millisecond.
    * Utilize Python's built-in `tracemalloc` library or basic OS process calls to track peak memory usage during execution runs.
    * Export these performance metrics alongside your quality scores so Person 4 can display resource-efficiency graphs on the user dashboard.
* **Component Deliverable:** `person_2/utils/profiler.py`.
* **Testing Gateway:** Verify that the timers and memory counters correctly catch and report resource deltas during execution.

---

### 📌 Day 14: System Stress-Testing & Edge Validation
* **Technical Objective:** Stress-test the engine against malformed input files, giant codebases, syntax errors, and missing files to guarantee that the system gracefully logs errors instead of crashing.
* **Algorithmic Blueprint:**
    * Create a collection of chaotic edge-case test assets designed to break parsers: files filled with random characters, deeply nested directories, massive file sizes, and scripts with broken syntax.
    * Run these broken assets through the evaluation loop and verify that your system-wide `try/except` guard rails catch the failures, log them securely, and return an error status rather than allowing the master process to crash.
* **Component Deliverable:** `person_2/tests/stress_harness.py`.
* **Testing Gateway:** Confirm that processing a completely corrupted file returns a valid validation failure response with an error code of 100% test survival rate.

---

### 📌 Day 15: Final Testing & Documentation Sync
* **Technical Objective:** Conduct a comprehensive review of the codebase, ensure code test coverage meets your target thresholds, and verify that the system is ready to be merged into the shared `develop` branch.
* **Algorithmic Blueprint:**
    * Run a complete test coverage audit using `pytest-cov` to ensure every execution branch and error condition is covered by your automated test suite.
    * Conduct an integration review with Person 1 and Person 4 to verify that API connection points, Pydantic data schemas, and data pipelines match perfectly.
    * Update all documentation logs inside the `documentation/person_2/` folder to reflect the final state of the system.
* **Component Deliverable:** Complete, production-ready `person_2` code architecture package.
* **Testing Gateway:** Run the entire test suite one last time to confirm a 100% passing rate across all test targets.

---

## 📈 System Flow & Processing Pipeline

The block diagram below details how code files move through your subsystem, starting from the raw input files and ending with the final schema export:

```text
[Raw Submission Workspace File Pack]
                 │
                 ▼
     ┌───────────────────────┐
     │   LanguageDetector    │ ──► Identifies Language Profiles (Python/JS/TS)
     └───────────────────────┘
                 │
                 ├──────────────────────────────────────┐
                 ▼                                      ▼
     ┌───────────────────────┐              ┌───────────────────────┐
     │  TreeSitterRegistry   │              │ LinterExecutionEngine │
     └───────────────────────┘              └───────────────────────┘
                 │                                      │
        (AST Node Generation)                  (Subprocess Invocation)
                 │                                      │
                 ├──────────────────────┐               │   (Ruff/ESLint CLI)
                 ▼                      ▼               ▼
     ┌───────────────────────┐  ┌───────────────┐ ┌─────────────────────┐
     │  CyclomaticComplexity  │  │  CodeSmell    │ │ Captures Errors &   │
     │      Calculator       │  │   Detector    │ │ Converts to Dict  │
     └───────────────────────┘  └───────────────┘ └─────────────────────┘
                 │                      │                       │
           (Complexity)            (smells list)         (violations)
                 │                      │                       │
                 └──────────────────────┼───────────────────────┘
                                        ▼
                           ┌─────────────────────────┐
                           │   Metrics Aggregator    │
                           └─────────────────────────┘
                                        │
                                (Assembles Data)
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │ Pydantic Schema Mapping │ ──► Export EvaluationResult
                           └─────────────────────────┘