import ast
import re
import logging

logger = logging.getLogger("OriginalityParser")

def normalize_ast(tree):
    """
    Walks the AST tree to collect parameters and local variable names,
    mapping them to generic names (arg_1, var_1, etc.) to eliminate rename obfuscation.
    Excludes Python built-ins, standard libraries, and method self/cls keywords.
    """
    exclude_names = {
        "self", "cls", "print", "len", "range", "str", "int", "float", "list", 
        "dict", "set", "tuple", "enumerate", "zip", "sum", "max", "min", "abs",
        "round", "any", "all", "map", "filter", "sorted", "reversed", "open",
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError"
    }
    
    arg_map = {}
    var_map = {}
    arg_counter = [1]
    var_counter = [1]

    # First Pass: Collect parameters and variables
    class NameCollector(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # Collect function arguments
            for arg in node.args.args:
                if arg.arg not in exclude_names and arg.arg not in arg_map:
                    arg_map[arg.arg] = f"arg_{arg_counter[0]}"
                    arg_counter[0] += 1
            for arg in node.args.kwonlyargs:
                if arg.arg not in exclude_names and arg.arg not in arg_map:
                    arg_map[arg.arg] = f"arg_{arg_counter[0]}"
                    arg_counter[0] += 1
            if node.args.vararg:
                if node.args.vararg.arg not in exclude_names and node.args.vararg.arg not in arg_map:
                    arg_map[node.args.vararg.arg] = f"arg_{arg_counter[0]}"
                    arg_counter[0] += 1
            if node.args.kwarg:
                if node.args.kwarg.arg not in exclude_names and node.args.kwarg.arg not in arg_map:
                    arg_map[node.args.kwarg.arg] = f"arg_{arg_counter[0]}"
                    arg_counter[0] += 1
            
            # Recurse inside the function body
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_Name(self, node):
            # Store contexts represent assignments (local variables)
            if isinstance(node.ctx, ast.Store):
                if node.id not in exclude_names and node.id not in arg_map and node.id not in var_map:
                    var_map[node.id] = f"var_{var_counter[0]}"
                    var_counter[0] += 1

        def visit_arg(self, node):
            # Comprehensions and lambdas parameters
            if node.arg not in exclude_names and node.arg not in arg_map:
                arg_map[node.arg] = f"arg_{arg_counter[0]}"
                arg_counter[0] += 1

    # Run collection pass
    NameCollector().visit(tree)

    # Second Pass: Transform identifiers in the AST
    class NameTransformer(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in arg_map:
                node.id = arg_map[node.id]
            elif node.id in var_map:
                node.id = var_map[node.id]
            return node

        def visit_arg(self, node):
            if node.arg in arg_map:
                node.arg = arg_map[node.arg]
            return node
            
        def visit_keyword(self, node):
            # Do not rename keyword names in function calls, only their values
            node.value = self.visit(node.value)
            return node

    NameTransformer().visit(tree)
    return tree

def clean_function_source(node):
    """
    Extracts the raw text of a function, removes docstrings, normalizes
    variable/parameter names using AST rewriting, and unparses it.
    """
    try:
        with open(node.filename, "r", encoding="utf-8") as f:
            full_source = f.read()
            
        raw_source = ast.get_source_segment(full_source, node)
        if not raw_source:
            return ""
            
        # Parse segment into individual AST node
        func_ast = ast.parse(raw_source)
        
        # 1. Strip docstrings at AST level
        for sub_node in ast.walk(func_ast):
            if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if sub_node.body and isinstance(sub_node.body[0], ast.Expr):
                    val = sub_node.body[0].value
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        sub_node.body.pop(0)
                        if not sub_node.body:
                            sub_node.body.append(ast.Pass())
                            
        # 2. Normalize AST variable names
        normalize_ast(func_ast)
        
        # 3. Unparse back to clean, standardized python source
        cleaned = ast.unparse(func_ast).strip()
        return cleaned
        
    except Exception as e:
        logger.warning(f"AST cleaning failed, falling back to regex: {e}")
        # Standard fallback to regex cleaning
        raw_segment = ast.get_source_segment(open(node.filename, "r").read(), node)
        cleaned = re.sub(re.compile(r"#.*?\n"), "\n", raw_segment)
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
        return cleaned

class FunctionExtractor(ast.NodeVisitor):
    """
    Traverses the AST tree depth-first, tracking the current class enclosing context
    and extracting nested function/method scopes.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions = []
        self.class_stack = []

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        func_name = node.name
        # Skip double underscore boilerplate methods except __init__
        if func_name.startswith("__") and func_name.endswith("__") and func_name != "__init__":
            return
            
        parent_class = self.class_stack[-1] if self.class_stack else None
        node.filename = self.file_path
        
        cleaned_code = clean_function_source(node)
        if cleaned_code:
            signature = f"def {parent_class}.{func_name}" if parent_class else f"def {func_name}"
            self.functions.append({
                "function_name": func_name,
                "signature": signature,
                "parent_class": parent_class,
                "cleaned_source": cleaned_code
            })
            
        # Support searching for nested function declarations inside this function
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        func_name = node.name
        if func_name.startswith("__") and func_name.endswith("__") and func_name != "__init__":
            return
            
        parent_class = self.class_stack[-1] if self.class_stack else None
        node.filename = self.file_path
        
        cleaned_code = clean_function_source(node)
        if cleaned_code:
            signature = f"async def {parent_class}.{func_name}" if parent_class else f"async def {func_name}"
            self.functions.append({
                "function_name": func_name,
                "signature": signature,
                "parent_class": parent_class,
                "cleaned_source": cleaned_code
            })
            
        self.generic_visit(node)

def extract_functions_from_file(file_path):
    """
    Parses a file and extracts all functions and methods using AST traversal.
    Tracks parent class scopes and applies variable normalization.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            
        tree = ast.parse(source_code, filename=file_path)
        extractor = FunctionExtractor(file_path)
        extractor.visit(tree)
        return extractor.functions

    except Exception as e:
        print(f"[Error] Error parsing AST for {file_path}: {e}")
        return []

# --- Quick Test Loop ---
if __name__ == "__main__":
    test_file = __file__
    print(f"[Parser] Normalizing and Slicing file: {test_file}\n")
    
    extracted = extract_functions_from_file(test_file)
    for index, func in enumerate(extracted, start=1):
        print(f"--- Function #{index}: {func['signature']} (Class: {func['parent_class']}) ---")
        print(func['cleaned_source'])
        print("-" * 40, "\n")