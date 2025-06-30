"""
Vercel serverless function entry point for Flask app
"""
from app import app

# Vercel expects a callable named 'handler'
handler = app