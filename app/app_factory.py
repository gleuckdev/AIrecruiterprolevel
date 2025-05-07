"""
Application Factory for AI Recruiter Pro

This module contains the factory function for creating a Flask application.
It handles configuration, extension initialization, blueprint registration,
and error handling setup.
"""

import os
import logging
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Create and configure the Flask application.

    Args:
        config_name (str, optional): The configuration to use (development,
            testing, production). Defaults to None, which uses the environment.

    Returns:
        Flask: The configured Flask application.
    """
    # Create the Flask application
    app = Flask(__name__)
    
    # Configure proxy settings for proper URL generation behind proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure the application
    configure_app(app, config_name)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize services
    initialize_services(app)
    
    return app


def configure_app(app, config_name=None):
    """
    Configure the Flask application with the appropriate settings.

    Args:
        app (Flask): The Flask application.
        config_name (str, optional): The configuration to use. Defaults to None.
    """
    # Default configuration
    app.config.from_object('app.config.DefaultConfig')
    
    # Environment-specific configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    if config_name == 'development':
        app.config.from_object('app.config.DevelopmentConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    elif config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    
    # Override with environment variables (if provided)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config['SECRET_KEY'])
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', app.config['SQLALCHEMY_DATABASE_URI'])
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = config_name == 'production'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800  # 30 minutes


def initialize_extensions(app):
    """
    Initialize Flask extensions.

    Args:
        app (Flask): The Flask application.
    """
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize Flask-JWT-Extended
    jwt.init_app(app)
    
    # Initialize CSRF protection
    csrf.init_app(app)


def register_blueprints(app):
    """
    Register Flask blueprints.

    Args:
        app (Flask): The Flask application.
    """
    # Import blueprints
    from app.routes.auth import auth_bp
    from app.routes.candidates import candidates_bp
    from app.routes.jobs import jobs_bp
    from app.routes.api import api_bp
    from app.routes.core import core_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(core_bp)


def configure_logging(app):
    """
    Configure logging for the application.

    Args:
        app (Flask): The Flask application.
    """
    # Set up logging
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Add file handler in production
    if not app.config['DEBUG']:
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)


def register_error_handlers(app):
    """
    Register error handlers for the application.

    Args:
        app (Flask): The Flask application.
    """
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def initialize_services(app):
    """
    Initialize application services.

    Args:
        app (Flask): The Flask application.
    """
    # Import and initialize service container
    from app.services import init_services
    init_services(app)