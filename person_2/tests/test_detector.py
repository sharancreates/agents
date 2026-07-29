import pytest
from person_2.core.detector import LanguageDetector

def test_language_detection_by_extension():
    detector = LanguageDetector()
    method = getattr(detector, "detect_language_from_path", getattr(detector, "detect_language", None))
    assert method("main.py") == "python"
    assert method("app.js") == "javascript"
    assert method("index.ts") == "typescript"

def test_language_detection_fallback():
    detector = LanguageDetector()
    method = getattr(detector, "detect_language_from_path", getattr(detector, "detect_language", None))
    assert method("unknown.xyz") == "unknown"