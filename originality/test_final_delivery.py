"""
Final Sprint Delivery Test Suite.
Verifies master release manifest generation and component checksum completeness.
"""

import os
import json
import tempfile
import shutil
from release_manager import ReleaseManager

def run_final_delivery_tests():
    print("=" * 60)
    print("RUNNING DAY 24: FINAL SPRINT DELIVERY VERIFICATION")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    try:
        # Create dummy component files for testing
        dummy_file = os.path.join(temp_dir, "cli.py")
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write("print('Release Verification Test')\n")

        manager = ReleaseManager(agent_dir=temp_dir)
        manifest_path = manager.export_manifest("TEST_MANIFEST.json")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Release Name: {data['sprint_name']}")
        print(f"Version: {data['version']}")
        print(f"Days Completed: {data['total_days_completed']} / 24")
        print(f"Components Checked: {len(data['components'])}")

        assert data["total_days_completed"] == 24
        assert data["version"] == "1.0.0-RELEASE"
        assert "cli.py" in data["components"]
        assert data["components"]["cli.py"]["status"] == "VERIFIED"

        print("-" * 60)
        print("ALL 24-DAY SPRINT DELIVERY CHECKS PASSED SUCCESSFULLY!")
        print("=" * 60)

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_final_delivery_tests()