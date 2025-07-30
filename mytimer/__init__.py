"""MyTimer package initialization."""

import os

# Disable HTTPie network update checks during tests or CLI usage
os.environ.setdefault("HTTPIE_DISABLE_UPGRADE_CHECK", "1")
