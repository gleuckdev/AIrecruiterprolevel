"""
Platform-aware configuration module for the AI Recruiter Pro Flask app.
Automatically adapts settings between Replit, Render, and local development environments.
"""

import logging
import os
import warnings
from datetime import timedelta

# Import flask only in the method that needs it
# This avoids circular imports during app initialization

# Set up logger
logger = logging.getLogger(__name__)


# Environment detection utilities
def is_running_on_replit():
    """Check if the application is running on Replit"""
    return "REPL_ID" in os.environ or "REPLIT" in os.environ


def is_running_on_render():
    """Check if the application is running on Render"""
    return "RENDER" in os.environ or "RENDER_EXTERNAL_URL" in os.environ


def is_running_on_cloud():
    """
    Check if the application is running in a cloud environment
    Currently detects: Replit, Render, Heroku, AWS, GCP, and Azure
    """
    cloud_indicators = [
        # Replit
        "REPL_ID",
        "REPLIT",
        # Render
        "RENDER",
        "RENDER_EXTERNAL_URL",
        # Heroku
        "DYNO",
        # AWS
        "AWS_REGION",
        "AWS_EXECUTION_ENV",
        # GCP
        "GOOGLE_CLOUD_PROJECT",
        # Azure
        "WEBSITE_SITE_NAME",
    ]

    return any(indicator in os.environ for indicator in cloud_indicators)


def get_environment_name():
    """
    Determine the environment name based on environment variables
    Returns: 'development', 'testing', or 'production'

    DEPRECATED: Use ConfigService.environment property instead.
    """
    # Import here to avoid circular imports
    from services.config_service import get_config

    config_service = get_config()
    return config_service.environment


def should_use_https():
    """
    Determine if the application should use HTTPS
    Returns: boolean

    DEPRECATED: Use ConfigService.should_use_https() instead.
    """
    # Import here to avoid circular imports
    from services.config_service import get_config

    config_service = get_config()
    return config_service.should_use_https()


class Config:
    # General settings
    SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV != "production"

    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_REFRESH_COOKIE_NAME = "refresh_token"
    JWT_COOKIE_SECURE = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True  # Enable JWT's built-in CSRF protection for cookie tokens
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Demo account credentials - secure handling
    # Only fallback to demo123 in development, not in production
    DEMO_PASSWORD = os.getenv(
        "DEMO_PASSWORD", "demo123" if get_environment_name() != "production" else None
    )

    # Cookie/session config
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Default; overridden below
    PREFERRED_URL_SCHEME = "http"

    # Session lifetime
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = False  # Allow CSRF token on HTTP in development
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour token lifetime

    # Schema validation settings
    VALIDATE_SCHEMA_ON_STARTUP = False  # Set to True to enable validation during startup
    STRICT_SCHEMA_VALIDATION = False  # Raise exception if validation fails
    WTF_CSRF_CHECK_DEFAULT = True

    # CSRF exempt paths (login endpoints shouldn't need CSRF protection)
    CSRF_EXEMPT_PATHS = [
        # JWT login-related endpoints
        "/auth/jwt/login",  # JWT login endpoint (POST)
        "/auth/jwt/signin",  # JWT login page (GET)
        "/auth/jwt/refresh",  # JWT token refresh endpoint
        "/auth/jwt/csrf-token",  # CSRF token endpoint
        "/auth/jwt/logout",  # JWT logout endpoint
        "/auth/jwt/signout",  # JWT signout page
        # Password reset endpoints
        "/auth/jwt/forgot-password",  # Forgot password form and submission
        "/auth/jwt/reset-password",  # Reset password with token
        # API auth endpoints
        "/api/v1/auth/",  # API v1 auth endpoints
        "/api/v2/auth/",  # API v2 auth endpoints
        # Additional endpoints to exempt if needed
        "/api/token",  # Any token-based API endpoint
        "/public/",  # Public endpoints
    ]  # Paths exempt from CSRF check
    CSRF_EXEMPT_API = True  # Exempt API endpoints from CSRF (they use JWT)

    # File upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}

    # Rate limiting
    RATE_LIMITS = {"auth": "5/minute", "jobs": "10/minute", "uploads": "10/minute"}

    # Database
    # Will be overridden by ConfigService.get("database_url") in app_factory.py
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # HTTPS and secure cookie configuration
    SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"

    @staticmethod
    def init_app(app):
        # Import modules here to avoid any potential issues with circular imports
        import os as os_local
        from logging.handlers import RotatingFileHandler

        # Use ConfigService for environment detection - consistent across the app
        from services.config_service import get_config

        config_service = get_config()

        is_replit = config_service.get("is_replit", False)
        is_cloud = config_service.get("is_cloud", False)
        is_render = config_service.get("is_render", False)

        # Get environment type
        env_name = config_service.environment
        is_production = config_service.is_production()

        # Determine HTTPS and cookie security settings
        use_https = config_service.should_use_https() or Config.SECURE_COOKIES

        # Set environment variables for consistent detection across the app
        os_local.environ["IS_REPLIT"] = str(is_replit).lower()
        os_local.environ["IS_CLOUD"] = str(is_cloud).lower()
        os_local.environ["APP_ENV"] = env_name

        # Add environment info to app config for easy access in templates
        app.config["IS_REPLIT"] = is_replit
        app.config["IS_CLOUD"] = is_cloud
        app.config["ENVIRONMENT"] = env_name

        # Enhanced logging for environment detection
        logger.info(
            f"Environment detection: Replit={is_replit}, Render={is_render}, Cloud={is_cloud}"
        )
        logger.info(f"Using environment: {env_name}")
        logger.info(
            f"HTTPS settings: use_https={use_https}, secure_cookies={Config.SECURE_COOKIES}"
        )

        # Configure centralized error logging
        if not app.debug:

            # Ensure logs directory exists with restricted permissions
            if not os_local.path.exists("logs"):
                os_local.makedirs("logs", exist_ok=True, mode=0o750)

            # Set up file handler for error logs
            error_handler = RotatingFileHandler(
                "logs/app_errors.log",
                maxBytes=10_000_000,  # 10MB max file size
                backupCount=5,  # Keep 5 backup files
            )
            error_handler.setLevel(logging.ERROR)

            # Configure formatter with detailed information for debugging
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"
            )
            error_handler.setFormatter(formatter)

            # Add the handler to the app logger
            app.logger.addHandler(error_handler)

            # Also set up a separate handler for API errors with more context
            api_handler = RotatingFileHandler(
                "logs/api_errors.log", maxBytes=10_000_000, backupCount=5
            )
            api_handler.setLevel(logging.ERROR)
            api_handler.setFormatter(formatter)

            # Get the OpenAI and embedding service loggers
            openai_logger = logging.getLogger("openai")
            embedding_logger = logging.getLogger("utils.embedding_service")
            resume_processor_logger = logging.getLogger("utils.resume_processor")

            # Add handlers to these loggers
            openai_logger.addHandler(api_handler)
            embedding_logger.addHandler(api_handler)
            resume_processor_logger.addHandler(api_handler)

            # Set propagation to ensure logs go up to the root logger
            openai_logger.propagate = True
            embedding_logger.propagate = True
            resume_processor_logger.propagate = True

        # Set secure cookies based on configuration and environment
        app.config["SESSION_COOKIE_SECURE"] = use_https
        app.config["PREFERRED_URL_SCHEME"] = "https" if use_https else "http"

        # Add force HTTPS middleware in production non-Replit environments if enabled
        if is_production and not is_replit and Config.FORCE_HTTPS:
            # Import Flask modules inside the function to avoid circular imports
            from flask import redirect, request

            @app.before_request
            def force_https():
                # Skip for some paths that don't need HTTPS (like healthchecks)
                if request.path.startswith("/health") or request.path.startswith("/.well-known/"):
                    return None

                # Check if request is already secure
                if not request.is_secure:
                    # Get the requested URL, replace http with https
                    url = request.url.replace("http://", "https://", 1)
                    # 301 is permanent redirect
                    return redirect(url, code=301)

        # Log environment detection results
        app.logger.info(f"Environment: REPLIT={is_replit}, PRODUCTION={is_production}")
        app.logger.info(f"Using secure cookies: {app.config['SESSION_COOKIE_SECURE']}")
        app.logger.info(f"Preferred URL scheme: {app.config['PREFERRED_URL_SCHEME']}")

        # Verify demo password configuration
        if not app.config.get("DEMO_PASSWORD"):
            if is_production:
                warnings.warn(
                    "⚠️ DEMO_PASSWORD is not set in production! Demo login will not work until this is configured in environment variables.",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                app.logger.info("Using default demo password in development environment")


# Development-specific configuration
class DevelopmentConfig(Config):
    DEBUG = True
    # Temporarily disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_CSRF_PROTECT = False

    # Enable schema validation in development
    VALIDATE_SCHEMA_ON_STARTUP = True
    STRICT_SCHEMA_VALIDATION = False  # Warning only, don't block startup


# Testing-specific configuration
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


# Production-specific configuration
class ProductionConfig(Config):
    DEBUG = False
    # Enable secure cookies and HTTPS by default in production
    SECURE_COOKIES = os.getenv("SECURE_COOKIES", "true").lower() == "true"
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "true").lower() == "true"


# Config dictionary for easy selection
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
