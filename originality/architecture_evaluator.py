import os
import sys
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[ARCH-EVAL] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ArchitectureEvaluator")

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Pluggable Anthropic client import
has_anthropic = False
try:
    from anthropic import Anthropic
    has_anthropic = True
except ImportError:
    logger.warning(
        "The 'anthropic' SDK is not installed in this environment. "
        "Please run: pip install anthropic\n"
        "The evaluator will run in simulation/mock mode."
    )

# Try importing GitignoreMatcher
try:
    from originality.pipeline import GitignoreMatcher
except ImportError:
    try:
        from pipeline import GitignoreMatcher
    except ImportError:
        # Fallback basic matcher
        class GitignoreMatcher:
            def __init__(self, root_dir: str):
                self.root_dir = Path(root_dir).resolve()
                self.default_ignores = {".git", "__pycache__", "venv", ".venv", "node_modules", ".idea", "dist", "build"}
            def is_ignored(self, file_path: str) -> bool:
                path = Path(file_path).resolve()
                for part in path.parts:
                    if part in self.default_ignores:
                        return True
                return False

# Generate deterministic ASCII tree representation
def generate_directory_tree(dir_path: str, matcher: GitignoreMatcher) -> str:
    lines = []
    root_path = Path(dir_path).resolve()
    
    def _walk(path: Path, prefix: str = ""):
        if matcher.is_ignored(str(path)):
            return
        try:
            items = sorted(list(path.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
        except Exception:
            return
            
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if matcher.is_ignored(str(item)):
                continue
                
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                next_prefix = prefix + ("    " if is_last else "│   ")
                _walk(item, next_prefix)
                
    lines.append(root_path.name)
    _walk(root_path)
    return "\n".join(lines)

# Collect manifest and README files
def collect_repository_metadata(dir_path: str, matcher: GitignoreMatcher) -> dict:
    root_path = Path(dir_path).resolve()
    data = {
        "readme": "",
        "manifests": {}
    }
    
    # README read
    readme_path = root_path / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                data["readme"] = f.read()[:5000] # Safe limit
        except Exception as e:
            logger.warning(f"Could not read README: {e}")
            
    # Manifest read
    manifests = ["requirements.txt", "package.json", "setup.py", "pyproject.toml", "Cargo.toml"]
    for manifest in manifests:
        m_path = root_path / manifest
        if m_path.exists():
            try:
                with open(m_path, "r", encoding="utf-8") as f:
                    data["manifests"][manifest] = f.read()[:3000]
            except Exception as e:
                logger.warning(f"Could not read manifest {manifest}: {e}")
                
    return data

SYSTEM_PROMPT = """
You are a Senior Systems Architecture Evaluator. Your role is to analyze a software repository's structural metadata (directory tree, dependency manifests, and README documentation) to evaluate design integrity, architectural novelty, and consistency.

You must analyze:
1. **Design Patterns**: Identify clean architecture traits, modular structure, or microservices patterns in the layout.
2. **Dependency & Build Consistency**: Cross-reference the directory layout against the manifest requirements (e.g. check if the manifest defines unused massive libraries, or if code imports libraries not declared in requirements).
3. **README Authenticity**: Assess if the README describes the actual structure accurately, or if it is a boilerplate template that does not match the file layout (indicating potential copy-paste plagiarism of code repositories).
4. **Scoring**: Provide architectural metrics:
    - Design Integrity (0.0 to 1.0)
    - Structural Novelty (0.0 to 1.0)
    - README Consistency (0.0 to 1.0)

You must output a strict JSON payload. Do not include any introductory or concluding text. Output raw JSON only. Use the following schema:
{
  "detected_patterns": ["Pattern1", "Pattern2"],
  "manifest_mismatches": ["Mismatch details here"],
  "readme_authenticity": "Authenticity evaluation comment",
  "scores": {
    "design_integrity": 0.90,
    "structural_novelty": 0.85,
    "readme_consistency": 0.95
  },
  "critique_summary": "Detailed technical architectural feedback"
}
"""

class ArchitectureEvaluator:
    @classmethod
    def evaluate_repository(cls, directory_path: str) -> dict:
        """
        Gathers structural details of the directory, builds the context payload,
        sends it to Claude via the Anthropic API, and returns the evaluation profile.
        """
        dir_path = Path(directory_path).resolve()
        logger.info(f"Gathering repository metadata for path: {dir_path}")
        
        matcher = GitignoreMatcher(str(dir_path))
        tree_str = generate_directory_tree(str(dir_path), matcher)
        metadata = collect_repository_metadata(str(dir_path), matcher)
        
        # Build prompt payload
        user_content = f"""
        Directory tree structure:
        ```
        {tree_str}
        ```
        
        Manifest files:
        {json.dumps(metadata['manifests'], indent=2)}
        
        README.md content:
        ```markdown
        {metadata['readme']}
        ```
        """
        
        # Load API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if has_anthropic and api_key:
            try:
                logger.info("Connecting to Anthropic API using Claude...")
                client = Anthropic(api_key=api_key)
                
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_content}
                    ]
                )
                
                # Parse response text to dict
                response_text = message.content[0].text.strip()
                return json.loads(response_text)
                
            except Exception as e:
                logger.error(f"Anthropic API call failed: {e}. Falling back to simulation.")
        
        # Fallback simulation/mock response
        logger.info("Running in SIMULATION mode (mock evaluation return).")
        
        # Basic heuristic metrics for local validation
        integrity = 0.95
        novelty = 0.75
        consistency = 1.0
        
        mismatches = []
        if "requirements.txt" not in metadata["manifests"]:
            mismatches.append("Missing requirements.txt dependency file.")
        if not metadata["readme"]:
            consistency = 0.2
            mismatches.append("Missing README.md project documentation.")
            
        simulated_response = {
          "detected_patterns": ["Modular Architecture", "Pipeline/Filter"],
          "manifest_mismatches": mismatches,
          "readme_authenticity": "Evaluated locally. Directory matches basic layout." if consistency > 0.5 else "Boilerplate/Missing README file.",
          "scores": {
            "design_integrity": integrity,
            "structural_novelty": novelty,
            "readme_consistency": consistency
          },
          "critique_summary": "Simulated output. Connect to Anthropic API to retrieve real Claude metrics."
        }
        return simulated_response

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate repository architecture structure.")
    parser.add_argument("--dir", default=".", help="Root path of the repository to analyze.")
    args = parser.parse_args()
    
    result = ArchitectureEvaluator.evaluate_repository(args.dir)
    print("\n" + "="*50)
    print("ARCHITECTURAL EVALUATION PROFILE:")
    print("="*50)
    print(json.dumps(result, indent=2))
    print("="*50 + "\n")
