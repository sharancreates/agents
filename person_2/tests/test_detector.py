import pytest
from person_2.core.detector import LanguageDetector

def test_language_detection_by_extension():
    detector = LanguageDetector()
    assert detector.detect("main.py") == "python"
    assert detector.detect("app.js") == "javascript"
    assert detector.detect("index.ts") == "typescript"

def test_language_detection_fallback():
    detector = LanguageDetector()
    assert detector.detect("unknown.xyz") == "unknown"