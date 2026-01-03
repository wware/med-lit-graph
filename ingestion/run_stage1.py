#!/usr/bin/env python3
"""
Wrapper script to run Stage 1 entity extraction.
Works both in Docker and locally.
"""

import sys
from pathlib import Path

# Determine if we're in Docker (/app) or local (ingestion/)
script_dir = Path(__file__).parent.absolute()

# Add current directory to path
sys.path.insert(0, str(script_dir))

# Import the stage module directly
# ruff: noqa: E402
import pipelines.stage1_entities as stage1  # noqa: E402

if __name__ == "__main__":
    stage1.main()
