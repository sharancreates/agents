import ast
import textwrap
import copy
from typing import List, Dict, Union

class CommentDocstringRemover(ast.NodeTransformer):
    """
    AST Transformer to remove docstrings and standalone block comments (string literals).
    """
    def visit_Expr(self, node: ast.Expr) -> Union[ast.Expr, None]:
        # Remove standalone string constants (docstrings and block comments)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node = self.generic_visit(node)
        if not node.body:
            node.body = [ast.Pass()]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        node = self.generic_visit(node)
        if not node.body:
            node.body = [ast.Pass()]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node = self.generic_visit(node)
        if not node.body:
            node.body = [ast.Pass()]
        return node


def clean_function_source(source: str) -> str:
    """
    Strips out single-line comments (#), multi-line block comments, docstrings,
    and normalizes excess whitespace from the given function source code.
    """
    # Dedent source code to handle indented blocks (e.g., methods from a class)
    dedented_source = textwrap.dedent(source)
    try:
        tree = ast.parse(dedented_source)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python source code: {e}")

    remover = CommentDocstringRemover()
    cleaned_tree = remover.visit(tree)
    ast.fix_missing_locations(cleaned_tree)

    # ast.unparse automatically removes comments and normalizes formatting/whitespace
    cleaned_source = ast.unparse(cleaned_tree).strip()
    return cleaned_source


def get_function_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """
    Extracts the clean function definition signature line.
    """
    node_copy = copy.deepcopy(node)
    # Clear body and decorators to isolate the signature line
    node_copy.body = [ast.Pass()]
    node_copy.decorator_list = []
    
    unparsed = ast.unparse(node_copy).strip()
    # Strip the trailing 'pass' keyword and excess whitespace
    if unparsed.endswith("pass"):
        unparsed = unparsed[:-4].strip()
    return unparsed


class FunctionExtractor(ast.NodeVisitor):
    """
    AST Visitor to traverse the AST of a Python file and extract top-level functions
    and class methods.
    """
    def __init__(self):
        self.functions: List[Dict[str, str]] = []
        self.class_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.handle_function(node)
        # Avoid traversing inside function bodies to prevent nested local functions from being extracted
        # as top-level functions or class methods.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.handle_function(node)

    def handle_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        if self.class_stack:
            # Class method
            full_name = ".".join(self.class_stack) + "." + node.name
        else:
            # Top-level functional module
            full_name = node.name

        # Extract the signature
        signature = get_function_signature(node)

        # Create a copy and clean comments/docstrings from the function itself
        node_copy = copy.deepcopy(node)
        remover = CommentDocstringRemover()
        cleaned_node = remover.visit(node_copy)
        ast.fix_missing_locations(cleaned_node)

        cleaned_source = ast.unparse(cleaned_node).strip()

        self.functions.append({
            "function_name": full_name,
            "signature": signature,
            "cleaned_source": cleaned_source
        })


def parse_source_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parses a Python source file and extracts all top-level functions and class methods
    with their comments/docstrings removed and whitespace normalized.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    
    extractor = FunctionExtractor()
    extractor.visit(tree)
    
    return extractor.functions


if __name__ == "__main__":
    import sys
    import json
    
    print("Testing parser against itself...")
    try:
        # Pass this script's own path to test splitting and cleaning performance
        funcs = parse_source_file(__file__)
        print(f"Successfully extracted {len(funcs)} functions/methods:")
        
        # Display the parsed output structure
        print(json.dumps(funcs, indent=4))
        
        # Self-verification check
        assert len(funcs) > 0, "No functions extracted!"
        print("\nSelf-test PASSED successfully!")
    except Exception as e:
        print(f"\nSelf-test FAILED: {e}", file=sys.stderr)
        sys.exit(1)
