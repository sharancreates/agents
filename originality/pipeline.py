import os
import argparse
import logging
import fnmatch
import hashlib
import random
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("OriginalityPipeline")

# Safe imports for parser and db_client
try:
    from originality.parser import extract_functions_from_file
    from originality.db_client import DatabaseManager
except ImportError:
    try:
        from parser import extract_functions_from_file
        from db_client import DatabaseManager
    except ImportError as e:
        logger.error(
            "Failed to import parser or db_client. Make sure to run the script "
            "from the 'agents' or 'agents/originality' directory."
        )
        raise e

class GitignoreMatcher:
    """
    A lightweight, self-contained parser and matcher for .gitignore files
    to prevent indexing virtual environments, cache folders, and ignored files.
    """
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.patterns = []
        
        # Default ignores to safeguard against huge directories if .gitignore is missing
        self.default_ignores = {".git", "__pycache__", "venv", ".venv", ".idea", "node_modules"}
        
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Ignore comments and empty lines
                        if line and not line.startswith("#"):
                            self.patterns.append(line)
                logger.info(f"[Matcher] Loaded {len(self.patterns)} ignore patterns from {gitignore_path}")
            except Exception as e:
                logger.warning(f"[Matcher] Error reading .gitignore: {e}")

    def is_ignored(self, file_path: str) -> bool:
        """
        Determines whether a file or directory path is ignored.
        """
        path = Path(file_path).resolve()
        
        # Resolve path relative to root directory
        try:
            rel_path = path.relative_to(self.root_dir)
        except ValueError:
            # Not under the root directory
            return True
            
        rel_path_str = rel_path.as_posix()

        # 1. Quick check for default folder exclusions in any part of the path
        for part in rel_path.parts:
            if part in self.default_ignores:
                return True

        # 2. Check against .gitignore patterns
        for pattern in self.patterns:
            is_dir_pattern = pattern.endswith('/')
            clean_pattern = pattern.rstrip('/')
            
            if is_dir_pattern:
                # Check if this directory occurs in the relative path
                if f"/{clean_pattern}/" in f"/{rel_path_str}/" or rel_path_str.startswith(clean_pattern + "/"):
                    return True
            else:
                # Direct name or glob match
                if fnmatch.fnmatch(rel_path_str, clean_pattern) or fnmatch.fnmatch(path.name, clean_pattern):
                    return True
                    
        return False

class EmbeddingClient:
    """
    A pluggable embedding client supporting local SentenceTransformers
    and falling back to deterministic, unit-normalized mock embeddings for validation.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.encoder = None
        
        if model_name == "all-MiniLM-L6-v2":
            self.dimension = 384
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[Embedding] Loading SentenceTransformer: '{model_name}'...")
                self.encoder = SentenceTransformer(model_name)
                logger.info("[Embedding] Model loaded successfully.")
            except ImportError:
                logger.warning(
                    "[Embedding] 'sentence-transformers' not installed. "
                    "Using deterministic hash-based mock embeddings (dim=384) for dry-run validation."
                )
        elif model_name == "text-embedding-3-small":
            self.dimension = 1536
            logger.warning(
                "[Embedding] 'text-embedding-3-small' selected. "
                "Using deterministic hash-based mock embeddings (dim=1536) for dry-run validation."
            )
        else:
            raise ValueError(f"Unsupported model name: {model_name}")

    def get_embedding(self, text: str) -> list:
        """
        Generates a vector embedding for the input text.
        """
        # If encoder is loaded, use it
        if self.encoder is not None:
            try:
                # Convert embedding array to list of floats
                embedding = self.encoder.encode(text).tolist()
                return embedding
            except Exception as e:
                logger.error(f"[Embedding] Error during model encoding: {e}. Falling back to mock.")

        # Deterministic, unit-normalized hash-based fallback embedding
        return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> list:
        """
        Generates a unit-normalized, deterministic mock embedding based on input text hash.
        This allows testing indexing, upserts, and Cosine similarity without network or PyTorch deps.
        """
        # Hash text to seed random generator
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hash_bytes, byteorder="big")
        rng = random.Random(seed)
        
        # Generate random vector
        raw_vector = [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        
        # L2 Normalize the vector to unit length (important for cosine/inner-product calculations)
        magnitude = sum(x * x for x in raw_vector) ** 0.5
        if magnitude == 0:
            return [0.0] * self.dimension
        return [x / magnitude for x in raw_vector]

def process_codebase_pipeline(directory_path: str, model_name: str = "all-MiniLM-L6-v2"):
    """
    Main orchestration function to crawl directories, skip ignored paths,
    parse files, encode source code, and upsert records to pgvector.
    """
    root_dir = Path(directory_path).resolve()
    logger.info(f"[Pipeline] Starting integration pipeline on: {root_dir}")
    
    # Initialize components
    matcher = GitignoreMatcher(str(root_dir))
    embedder = EmbeddingClient(model_name=model_name)
    
    # Setup database schema with matching dimension
    try:
        DatabaseManager.setup_schema(vector_dim=embedder.dimension)
    except Exception as e:
        logger.error(f"[Pipeline] Database connection failed. Ensure Docker is running. Error: {e}")
        return

    # Statistics tracking
    stats = {
        "files_scanned": 0,
        "files_parsed": 0,
        "files_skipped": 0,
        "functions_indexed": 0,
        "errors": 0
    }

    # Walk directory tree
    for root, dirs, files in os.walk(root_dir):
        # Filter directories in-place to avoid traversing ignored subtrees
        dirs[:] = [d for d in dirs if not matcher.is_ignored(os.path.join(root, d))]
        
        for file in files:
            stats["files_scanned"] += 1
            file_path = os.path.join(root, file)
            
            # We only index Python source files
            if not file.endswith(".py"):
                stats["files_skipped"] += 1
                continue
                
            if matcher.is_ignored(file_path):
                logger.info(f"[Pipeline] Skipped ignored file: {os.path.relpath(file_path, root_dir)}")
                stats["files_skipped"] += 1
                continue

            # Process file
            logger.info(f"[Pipeline] Parsing: {os.path.relpath(file_path, root_dir)}")
            try:
                # 1. Parse functions and methods
                functions = extract_functions_from_file(file_path)
                if not functions:
                    continue
                
                stats["files_parsed"] += 1
                
                # 2. Iterate and generate embeddings
                for func in functions:
                    func_name = func["function_name"]
                    signature = func["signature"]
                    cleaned_code = func["cleaned_source"]
                    
                    # Compute vector embedding
                    embedding = embedder.get_embedding(cleaned_code)
                    
                    # 3. Upsert to the PostgreSQL database
                    relative_path = os.path.relpath(file_path, root_dir)
                    DatabaseManager.upsert_function_embedding(
                        file_path=relative_path,
                        function_name=func_name,
                        signature=signature,
                        cleaned_source=cleaned_code,
                        embedding=embedding
                    )
                    stats["functions_indexed"] += 1
                    
            except Exception as e:
                logger.error(f"[Pipeline] Failed to process {file}: {e}")
                stats["errors"] += 1

    # Print summary reports
    logger.info("================ Pipeline Execution Report ================")
    logger.info(f"  Total Files Scanned   : {stats['files_scanned']}")
    logger.info(f"  Python Files Parsed   : {stats['files_parsed']}")
    logger.info(f"  Files/Folders Skipped : {stats['files_skipped']}")
    logger.info(f"  Functions Indexed     : {stats['functions_indexed']}")
    logger.info(f"  Exceptions Handled    : {stats['errors']}")
    logger.info("===========================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrator pipeline for indexing codebase vectors.")
    parser.add_argument(
        "--dir", 
        default=".", 
        help="Path to the root directory of the codebase to index."
    )
    parser.add_argument(
        "--model", 
        default="all-MiniLM-L6-v2", 
        choices=["all-MiniLM-L6-v2", "text-embedding-3-small"],
        help="Embedding model name to use."
    )
    args = parser.parse_args()

    process_codebase_pipeline(directory_path=args.dir, model_name=args.model)
