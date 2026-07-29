import pytest
from person_2.core.detector import LanguageDetector

def test_language_detection_by_extension():
    detector = LanguageDetector()
    assert detector.detect_language("main.py") == "python"
    assert detector.detect_language("app.js") == "javascript"
    assert detector.detect_language("index.ts") == "typescript"

def test_language_detection_fallback():
    detector = LanguageDetector()
    assert detector.detect_language("unknown.xyz") == "unknown"