#!/usr/bin/env python3
"""Bot entrypoint with SSL verification disabled"""
import ssl
import sys
from pathlib import Path

# Disable SSL verification BEFORE importing anything that uses requests
ssl._create_default_https_context = ssl._create_unverified_context

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import the main run module
from run import main

if __name__ == "__main__":
    main()
