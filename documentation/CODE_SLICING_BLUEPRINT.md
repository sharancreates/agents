# Technical Blueprint: Fine-grained Code Slicing & AST Normalization

This blueprint outlines the AST (Abstract Syntax Tree) transformation strategies and parent-class context-tracking mechanisms used by the Originality Agent on Day 7 of the engineering sprint.

---

## 1. Normalization Strategies (Eliminating Identifier-Rename Obfuscation)

Simple search engines can be defeated by renaming arguments and local variables. To solve this, we parse function code segments into a Python AST, identify localized identifiers, and rewrite them to a standardized format:

1.  **Parameter Extraction**: Parameters (positional, keyword-only, `*args`, `**kwargs`) inside the function's parameter list are cataloged.
2.  **Local Variables**: Any identifier assigned to inside the function body (`ast.Store` context) is classified as a local variable.
3.  **Excluded Globals / Built-ins**:
    *   `self` and `cls` are excluded to preserve standard object-oriented signatures.
    *   Python built-in functions (e.g., `print`, `len`, `range`, `zip`) are excluded to preserve standard library interactions.
    *   Standard exception classes (e.g., `Exception`, `ValueError`) are excluded.
4.  **AST Rewriting**:
    *   All parameter identifiers are mapped sequentially to generic tokens (`arg_1`, `arg_2`, etc.).
    *   All local variable identifiers are mapped sequentially to generic tokens (`var_1`, `var_2`, etc.).
    *   References to these variables (in Load/Store contexts) are updated.
    *   Keyword argument keys in function calls (e.g. `x` in `foo(x=y)`) are preserved; only their values are transformed.
5.  **Standardized Generation**: The transformed AST is unparsed back into Python source via `ast.unparse()`. Comments are naturally discarded during parsing, and docstrings are removed at the AST level, ensuring the resulting string is pure normalized code.

---

## 2. Parent Scope & Signature Formats

Instead of treating codebases as a flat directory of files, files are traversed depth-first using a subclassed `ast.NodeVisitor`. This allows us to track class contexts via a stack:

*   **Top-level Functions**:
    *   Signature format: `def function_name`
    *   Parent class: `None`
*   **Class Methods**:
    *   Signature format: `def ClassName.method_name`
    *   Parent class: `ClassName`
*   **Enclosed Async Functions**:
    *   Signature format: `async def ClassName.method_name` or `async def function_name`

---

## 3. Edge-Case & Deeply Nested Structure Handling

*   **Recursive Calls**: The function's own name is a module-level or class-level declaration (not defined via a local store or parameter list). Consequently, recursive references (e.g. `calculate_factorial(n-1)`) keep their original name, maintaining proper semantic linkage.
*   **Nested Classes and Functions**: The depth-first `ast.NodeVisitor` pushes classes onto a `class_stack` dynamically. If a class is declared inside another class, it formats the parent context as a nested stack element (e.g., `def EnclosingClass.NestedClass.method_name`), preserving deep hierarchy scopes.
*   **Syntax Fallbacks**: If a code segment contains invalid syntax or is partial, the normalizer falls back gracefully to a regex-based comment-stripping cleaner to prevent pipeline blockages.

---

## 4. Implementation Location
The AST parser and normalization logic resides in the repository at: [parser.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/parser.py)
