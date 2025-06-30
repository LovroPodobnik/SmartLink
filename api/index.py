"""
Vercel serverless function entry point for Flask app
"""
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as application

# This is what Vercel expects
app = application