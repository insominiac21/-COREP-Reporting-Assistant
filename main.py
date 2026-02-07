"""Vercel entry point"""
import sys
from pathlib import Path

# Add root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from corep_assistant.server.api import app
from corep_assistant.server import ui  # Register UI routes

# Export for Vercel
# Vercel's @vercel/python builder looks for an 'app' or 'application' object.
app = app
