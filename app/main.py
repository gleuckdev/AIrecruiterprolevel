"""
Main application module for AI Recruiter Pro.

This is the entry point for the application. It uses the application factory
to create a Flask app with all necessary configuration and extensions.
"""

import os
from app.app_factory import create_app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Run the app in development mode
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])