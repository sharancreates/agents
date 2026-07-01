import os
import pytest
from agents.person_2.core.detector import LanguageDetector

def test_identify_file_by_extension(tmp_path):
    python_stub = tmp_path / "main.py"
    python_stub.write_text("import sys\nprint('hello')", encoding="utf-8")
    assert LanguageDetector.identify_file(str(python_stub)) == "python"

def test_identify_file_by_shebang(tmp_path):
    executable_stub = tmp_path / "runner"
    executable_stub.write_text("#!/usr/bin/env node\nconsole.log(1);", encoding="utf-8")
    assert LanguageDetector.identify_file(str(executable_stub)) == "javascript"