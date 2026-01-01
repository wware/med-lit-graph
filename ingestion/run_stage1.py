#!/usr/bin/env python3
"""
Wrapper script to run Stage 1 entity extraction.
Works both in Docker and locally.
"""

import sys
from pathlib import Path

# Add ingestion directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import and run the stage
from pipelines import stage1_entities

if __name__ == "__main__":
    stage1_entities.main()
