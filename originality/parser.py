import ast
import re

def clean_function_source(node):
    """
    Extracts the raw text of a function, removes comments and docstrings 
    to prevent simple obfuscation from tricking the embedding model.
    """
    # Get the raw source code of the function node
    raw_source = ast.get_source_segment(open(node.filename, "r").read(), node)
    if not raw_source:
        return ""

    # Parse it back to easily extract/remove docstrings
    try:
        func_ast = ast.parse(raw_source)
        for sub_node in ast.walk(func_ast):
            if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # If there's a docstring, remove its string value from the text
                docstring = ast.get_docstring(sub_node)
                if docstring:
                    raw_source = raw_source.replace(f'"""{docstring}"""', '')
                    raw_source = raw_source.replace(f"'''{docstring}'''", '')
    except Exception:
        pass # Fallback to regex cleaning if ast parsing a fragment fails

    # Regex to remove single line comments (# ...)
    cleaned = re.sub(re.compile(r"#.*?\n"), "\n", raw_source)
    
    # Minimize extra whitespace lines
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def extract_functions_from_file(file_path):
    """
    Parses a file and extracts all top-level functions and class methods.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            
        tree = ast.parse(source_code, filename=file_path)
        functions_extracted = []

        for node in ast.walk(tree):
            # Inject filename reference into node so ast.get_source_segment works smoothly
            node.filename = file_path 
            
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                # Skip simple init files or boilerplate dunder functions if needed
                if func_name.startswith("__") and func_name.endswith("__") and func_name != "__init__":
                    continue
                    
                cleaned_code = clean_function_source(node)
                if cleaned_code:
                    functions_extracted.append({
                        "function_name": func_name,
                        "signature": f"def {func_name}",
                        "cleaned_source": cleaned_code
                    })
        return functions_extracted

    except Exception as e:
        print(f"❌ Error parsing AST for {file_path}: {e}")
        return []

# --- Quick Test Loop ---
if __name__ == "__main__":
    # Let's test it on its own file!
    test_file = __file__
    print(f"🔍 Slicing file: {test_file}\n")
    
    extracted = extract_functions_from_file(test_file)
    for index, func in enumerate(extracted, start=1):
        print(f"--- Function #{index}: {func['function_name']} ---")
        print(func['cleaned_source'])
        print("-" * 40, "\n")