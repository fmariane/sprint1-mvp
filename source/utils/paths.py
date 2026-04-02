"""Project paths (charts output, etc.)."""

from pathlib import Path

# sprint1-mvp/ (parent of source/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHARTS_DIR = PROJECT_ROOT / "charts"
