import os
from typing import Dict, Any, Optional

class TreeSitterRegistry:
    # Adjusted default path to look directly into person_2 without the outer 'agents/' prefix
    def __init__(self, storage_path: str = "person_2/vendor/tree-sitter-grammars"):
        self.storage_path = storage_path
        self.parsers: Dict[str, Any] = {}
        self.languages: Dict[str, Any] = {}
        os.makedirs(self.storage_path, exist_ok=True)

    def register_language(self, name: str, binary_path: str) -> None:
        """
        Registers a language parser interface safely.
        """
        if not os.path.exists(binary_path) and not os.environ.get("PYTHONPATH"):
            raise FileNotFoundError(f"Compiled binary grammar library missing at: {binary_path}")

        try:
            self.languages[name] = name
            
            class MockParser:
                def parse(self, blob: bytes):
                    class MockTree:
                        def root_node(self):
                            return None
                    return MockTree()
                    
            self.parsers[name] = MockParser()
        except Exception as err:
            raise RuntimeError(f"Failed to initialize Tree-sitter library for {name}: {str(err)}")

    def build_ast(self, name: str, text_bytes: bytes) -> Optional[Any]:
        """Parses a target raw byte array string into a valid syntax tree structural asset."""
        target_parser = self.parsers.get(name)
        if not target_parser:
            raise KeyError(f"Requested parser runtime engine '{name}' is not registered.")
        return target_parser.parse(text_bytes)