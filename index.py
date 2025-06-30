"""
Main entry point for Vercel deployment
This file must be in the root directory for Vercel
"""
from app import app

# Vercel will look for an 'app' variable
if __name__ == "__main__":
    app.run()