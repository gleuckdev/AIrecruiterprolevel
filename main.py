"""
Main application entry point for AI Recruiter Pro.

This file is the top-level entry point for running the application,
importing the Flask app from the app package.
"""

from app.main import app

if __name__ == '__main__':
    app.run()