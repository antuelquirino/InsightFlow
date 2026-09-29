"""Guards for repo-level decisions recorded in CLAUDE.md."""
from pathlib import Path

import yaml

WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def test_no_scheduled_workflows():
    # Data is generated once, by hand; nothing may run on a schedule.
    for workflow in WORKFLOWS_DIR.glob("*.yml"):
        config = yaml.safe_load(workflow.read_text())
        # PyYAML reads the bare key `on` as the boolean True.
        triggers = config.get("on", config.get(True)) or {}
        assert "schedule" not in triggers, f"{workflow.name} has a schedule trigger"
