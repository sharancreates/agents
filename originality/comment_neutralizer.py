import io
import re
import tokenize
import unicodedata
import logging

logger = logging.getLogger("CommentNeutralizer")

class CommentNeutralizer:
    # Patterns targeting Devanagari, Gujarati, and general non-ASCII characters
    NON_ASCII_PATTERN = re.compile(r"[^\x00-\x7F]+")

    @classmethod
    def neutralize_source_code(cls, source_code: str) -> str:
        """
        Processes python source code:
        - Normalizes Unicode representations to canonical NFKC form.
        - Tokenizes python statements to preserve indentation and code structures.
        - Identifies comments and docstrings containing non-ASCII scripts.
        - Strips/neutralizes non-English comments to avoid skewing similarity metrics.
        """
        if not source_code.strip():
            return source_code
            
        # 1. NFKC Unicode Normalization
        normalized = unicodedata.normalize("NFKC", source_code)
        
        # 2. Tokenize and strip foreign comments
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(normalized).readline))
        except Exception as e:
            logger.warning(f"Tokenizer failure during neutralization: {e}. Running regex fallback.")
            return cls.neutralize_regex_fallback(normalized)
            
        out = []
        last_row = 1
        last_col = 0
        
        for tok in tokens:
            tok_type = tok.type
            tok_string = tok.string
            start_row, start_col = tok.start
            end_row, end_col = tok.end
            
            # Preserve spacing and indentation alignments
            if start_row > last_row:
                out.append("\n" * (start_row - last_row))
                last_col = 0
            if start_col > last_col:
                out.append(" " * (start_col - last_col))
                
            # Perform neutralization
            if tok_type == tokenize.COMMENT:
                # If comment contains non-ASCII characters (e.g. Hindi, Gujarati)
                if cls.NON_ASCII_PATTERN.search(tok_string):
                    tok_string = "#"  # Replace with a blank placeholder
            elif tok_type == tokenize.STRING:
                # Identify if token is a docstring (multi-line triple quotes)
                is_docstring = (
                    tok_string.startswith('"""') or 
                    tok_string.startswith("'''") or
                    tok_string.startswith('r"""') or
                    tok_string.startswith("r'''")
                )
                if is_docstring and cls.NON_ASCII_PATTERN.search(tok_string):
                    tok_string = '""" neutralized docstring """'
                    
            out.append(tok_string)
            last_row = end_row
            last_col = end_col
            
        return "".join(out)

    @classmethod
    def neutralize_regex_fallback(cls, source_code: str) -> str:
        """
        Regex-based line scanner fallback in case of parsing exceptions.
        """
        lines = source_code.splitlines()
        cleaned = []
        for line in lines:
            if "#" in line:
                parts = line.split("#", 1)
                comment = parts[1]
                if cls.NON_ASCII_PATTERN.search(comment):
                    # Replace comment segment
                    line = parts[0] + "#"
            cleaned.append(line)
        return "\n".join(cleaned)
