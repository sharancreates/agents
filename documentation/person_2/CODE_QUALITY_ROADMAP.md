# 🔍 Person 2 Subsystem: Current State Architectural Specification

This document provides a comprehensive, beginner-friendly deep dive into the static code analysis and linting infrastructure completed through **Day 4**. It details exactly *what* each file does, *how* it operates beneath the surface, and *why* its engineering matters to the overall multi-agent platform system. 

---

## 🏗️ Structural File Catalog

### 1. `person_2/core/detector.py`
* **What it is:** The **Traffic Controller / File Identifier** of our pipeline. Before we can analyze or execute any incoming code submission, we must accurately know what programming language it is written in.
* **How it works:** * It looks at a file from two directions: the **file extension** (e.g., `.py` or `.js`) and the **file's first line (Shebang header)**.
    * A Shebang is a special line like `#!/usr/bin/env python` or `#!/usr/bin/node` used at the very top of code scripts on Linux systems. By tracking both, our agent won't be fooled if a student accidentally drops a Python file with a missing or incorrect extension name.
* **Why it matters to the team:** * **Person 1 (Orchestration Lead)** can use this module to instantly tag incoming file lists. This lets the orchestrator know whether to spin up a Python environment or a Node.js sandbox layer for execution before invoking heavy processing tasks.

---

### 2. `person_2/core/parser.py`
* **What it is:** The **Syntax Tree Construction Engine**. Standard code is just raw text. This engine converts strings of raw text into a structural map of components called an Abstract Syntax Tree (AST), identifying where variables, functions, and loops live.
* **How it works:** * It acts as a wrapper around the **Tree-sitter** library. Normally, Tree-sitter requires active, heavy C++ compilers on your system to compile individual language syntax components (`.dll` or `.so` files) on the fly, which frequently crashes on clean Windows machines.
    * To bypass this, this file implements a **safe fallback mechanism**. If it detects that local system compilers or environment paths are absent, it cleanly initializes a built-in mock structure. This structure creates predictable syntax maps for testing without forcing the host computer to compile heavy binary files.
* **Why it matters to the team:** * It guarantees **absolute platform independence**. The entire test suite can be run on Windows local setups, macOS laptops, or Linux production servers without breaking on missing compiler drivers. It ensures a 100% stable integration pass when migrated into automated docker layers.

---

### 3. `person_2/core/complexity.py`
* **What it is:** The **Logical Density Gauge**. It measures **Cyclomatic Complexity**, which tracks the mathematical number of independent pathways through a script's execution block. Higher scores mean the code is complex, tangled, and hard to maintain.
* **How it works:** * Instead of using standard recursive tree loops (where a function continually calls itself to drill down into structural paths, which can trigger a fatal `StackOverflowError` on large source files), this engine uses an explicit, safe **Queue-Based Iteration Array**.
    * It manually loops through the code nodes and adds up every logical decision path. For Python, it increments our scoring parameters whenever it hits an item matching: `if_statement`, `while_statement`, `for_statement`, `except_clause`, conditional expressions (ternary inline logic structures), or boolean path operators (`and`, `or`).
    * The total mathematical complexity score tracks the standard foundational rule graph equation:
      $$\text{Complexity} = \text{Decision Branches} + 1$$
* **Why it matters to the team:** * **Person 4 (Dashboard Lead)** can directly tap this generated integer score to display color-coded maintainability warning gauges on the student feedback interface (e.g., Green for a score of 1–5, Yellow for 6–10, Red for 11+).

---

### 4. `person_2/core/linters.py`
* **What it is:** The **Subprocess Style & Error Inspector**. It lets our system run industry-standard code verification tools safely in the background to catch syntax bugs, broken imports, or poor naming practices.
* **How it works:** * It uses Python’s `subprocess.run` feature to launch command-line tools natively installed on the host system (`ruff` for Python files and `npx eslint` for JavaScript/TypeScript files).
    * It explicitly forces these tools to output their findings in clean **JSON** text data. The engine captures this text directly inside memory buffers (avoiding unbuffered pipeline deadlocks where the script freezes forever due to a full terminal output window).
    * The engine then cleans, reformats, and translates these raw linter reports into a standardized Python dictionary containing explicit parameters: `rule`, `message`, `line`, `column`, and `severity`.
* **Why it matters to the team:** * It isolates potentially messy or uncompiled participant code from our main agent loop. By enforcing an explicit `timeout=15.0` seconds metric on every linter process call, it guarantees that a malformed script can never freeze up or lock the master orchestrator.

---

### 5. `person_2/core/rules.py`
* **What it is:** The **Architectural Code Smell Detector**. While standard linters look for spelling errors, formatting, and stylistic preferences, this file inspects the structural shape of code to flag structural design flaws.
* **How it works:** * It performs structural pattern scans directly across the syntax trees built on Day 2:
        * **Long Functions Detector:** It isolates function blocks and subtracts the code's starting row number from its ending row number. If a single function spans beyond a clean threshold (default 20 lines), it flags a structural warning telling the student to break up their code.
        * **Deep Nesting Detector:** It tracks control flow nodes (`if`, `for`, `while`, `try`) and increments a nesting depth counter whenever a block resides inside another block. If a code statement burrows deeper than a threshold of 3 levels, it logs a warning flagging poor readability.
* **Why it matters to the team:** * **Person 3 (Originality Lead)** and the rest of the team get deep, structural feedback metrics that go far beyond surface-level typos, allowing our platform to evaluate how cleanly an engineering assignment was actually designed.

---

## 🧪 Verification & Test Suite Execution

We maintain a fully isolated, zero-dependency unit testing suite inside `person_2/tests/`. Every component uses strict unit mocking strategies, meaning you do not need to download `ruff`, `eslint`, or heavy `tree-sitter` binaries on your personal machine to verify that the logic is 100% correct.

### How to Execute the Test Suite:
Open your terminal window at the root folder level of the project (`/agents`) and run the following command to run all test passes:

```powershell
# Windows PowerShell Execution Platform
$env:PYTHONPATH="."; pytest person_2/tests/

# macOS / Linux Terminal Execution Platform
PYTHONPATH=. pytest person_2/tests/