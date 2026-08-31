"""
Vercel Python entry point for AEGIS backend.
This file is auto-detected by Vercel's Python runtime.
"""
import sys
import os

# Add the src directory to Python path so we can import the aegis package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from aegis.api import app  # noqa: F401