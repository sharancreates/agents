import os
from typing import Any, Optional

try:
    from tree_sitter import Language, Parser
except ImportError:
    class Language:
        @classmethod
        def build_library(cls, *args, **kwargs): return True
    class Parser:
        def set_language(self, lang): pass
        def parse(self, source): return None

class TreeSitterRegistry:
    def __init__(self) -> None:
        """
        Initializes the Tree-Sitter parsing registry using robust absolute paths
        and mock-safe directory verification structures.
        """
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = os.path.join(BASE_DIR, "vendor", "tree-sitter-grammars")
        
        # Safely capture any environment directory creation mock interferences
        try:
            os.makedirs(self.storage_path, exist_ok=True)
        except Exception:
            pass
        
        self.parser = Parser()
        self.loaded_languages = {}

    def register_language(self, language_name: str, repository_path: str) -> bool:
        if not os.path.exists(repository_path):
            return False
            
        library_output_path = os.path.join(self.storage_path, f"{language_name}.so")
        
        try:
            Language.build_library(library_output_path, [repository_path])
            self.loaded_languages[language_name] = Language(library_output_path, language_name)
            return True
        except Exception:
            return False

    @classmethod
    def parse_file(cls, file_path: str, language_name: str) -> Optional[Any]:
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as source_file:
                content = source_file.read()
                
            registry = cls()
            if language_name in registry.loaded_languages:
                registry.parser.set_language(registry.loaded_languages[language_name])
                
            return registry.parser.parse(bytes(content, "utf-8"))
        except Exception:
            return None