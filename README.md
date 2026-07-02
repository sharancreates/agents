# agents

# Code Quality & Functionality Subsystem (Person 2)

This directory contains the core static analysis and code execution subsystems managed by **Person 2**. It provides autonomous language identification, concrete syntax tree generation via Tree-sitter, abstract syntax tree traversal to compute structural metrics like Cyclomatic Complexity, and subprocess orchestration for external linters.

---

## 📂 Subsystem Layout

```text
person_2/
├── core/
│   ├── complexity.py       # AST branching node analyzer (Cyclomatic Complexity)
│   ├── detector.py         # File & workspace language classifier (Extension + Shebang)
│   ├── linters.py          # Subprocess Linter Execution Engine (Ruff + ESLint)
│   ├── parser.py           # Cross-platform safe Tree-sitter registry engine
│   └── rules.py            # AST Code Smell Rule Engine (Long Functions + Deep Nesting)
├── models/
│   └── schemas.py          # Strict Pydantic structures matching EvaluationResult
└── tests/
    ├── test_complexity.py  # Unit assertions for branch calculations
    ├── test_detector.py    # Language isolation environment tests
    ├── test_linters.py     # Subprocess output extraction tests
    ├── test_parser.py      # Registry mock mapping validations
    └── test_rules.py       # Unit assertions for structural rules