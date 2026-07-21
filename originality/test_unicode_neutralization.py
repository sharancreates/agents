import os
import sys
import ast
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[UNICODE-TEST] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnicodeNeutralizerTester")

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from originality.comment_neutralizer import CommentNeutralizer
except ImportError:
    try:
        from comment_neutralizer import CommentNeutralizer
    except ImportError as e:
        logger.error("Failed to import CommentNeutralizer.")
        raise e

def run_unicode_test_suite():
    # Reconfigure stdout to prevent encoding errors on Windows consoles when printing unicode
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    logger.info("Initializing Unicode comment neutralization test suite...")

    # Multi-lingual code containing Hindi, Gujarati, and English comments/docstrings
    raw_code_sample = """# English comment: main profile function
def process_user_data(username):
    \"\"\"
    ગુજરાતી ભાષામાં આ એક દસ્તાવેજીકરણ છે.
    This docstring is multi-lingual.
    \"\"\"
    # Hindi comment: उपयोगकर्ता प्रोफ़ाइल प्राप्त करें
    profile = get_profile(username)  # Gujarati comment: અહીં પ્રોફાઇલ મેળવો
    
    # English comment: verify access
    if profile.is_valid:
        return True
    return False
"""

    logger.info("Executing neutralization on multi-lingual sample...")
    neutralized = CommentNeutralizer.neutralize_source_code(raw_code_sample)
    
    print("\n" + "="*60)
    print("ORIGINAL CODE SAMPLE:")
    print("="*60)
    print(raw_code_sample)
    
    print("\n" + "="*60)
    print("NEUTRALIZED CODE SAMPLE:")
    print("="*60)
    print(neutralized)
    print("="*60 + "\n")

    # Assertions
    # 1. English comments must be preserved
    assert "# English comment: main profile function" in neutralized, "English comments should be preserved."
    assert "# English comment: verify access" in neutralized, "English comments should be preserved."
    
    # 2. Hindi comments must be neutralized
    assert "उपयोगकर्ता प्रोफ़ાઇલ प्राप्त करें" not in neutralized, "Hindi comments must be stripped."
    
    # 3. Gujarati comments must be neutralized
    assert "અહીં પ્રોફાઇલ મેળવો" not in neutralized, "Gujarati comments must be stripped."
    
    # 4. Multi-lingual docstrings containing non-ASCII must be replaced
    assert "ગુજરાતી ભાષામાં આ એક દસ્તાવેજીકરણ છે" not in neutralized, "Non-ASCII docstring must be stripped."
    assert '""" neutralized docstring """' in neutralized, "Non-ASCII docstring should be replaced by placeholder."

    # 5. Verify the code compiles cleanly to an AST
    try:
        ast.parse(neutralized)
        logger.info("Neutralized output successfully compiled into Python AST.")
        compiled_ok = True
    except Exception as e:
        logger.error(f"Neutralized code failed AST compilation: {e}")
        compiled_ok = False
        
    assert compiled_ok, "Neutralized code must compile to valid AST."
    logger.info("Unicode neutralization stress tests completed successfully.")

if __name__ == "__main__":
    run_unicode_test_suite()
