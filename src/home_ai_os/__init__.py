"""Home AI OS - AI-Native Linux Desktop Environment."""

__version__ = "0.2.0"
__author__ = "Ryan Hamilton"

from pathlib import Path

# Base directories
HOME_AI_DIR = Path.home() / ".home_ai"
CONFIG_DIR = HOME_AI_DIR / "config"
DATA_DIR = HOME_AI_DIR / "data"
LOGS_DIR = HOME_AI_DIR / "logs"
CACHE_DIR = HOME_AI_DIR / "cache"

# Create directories
for directory in [HOME_AI_DIR, CONFIG_DIR, DATA_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
