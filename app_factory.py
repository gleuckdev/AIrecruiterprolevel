"""
Flask Application Factory

This module contains the factory function for creating a Flask application instance.
It centralizes app creation and configuration, separating it from routes and business logic.

It uses late imports for Flask-dependent modules to avoid circular imports and improve
testability. The application context is properly managed within each function to ensure
all operations are isolated.
"""

import logging
import os
from datetime import timedelta
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)

# Import non-Flask dependent modules
from config import config
from di.setup import setup_container


# Helper functions to modularize app initialization
def _initialize_logging(app):
    """Initialize unified logging system for the application"""
    # Set up structured logging
    log_level = app.config.get("LOG_LEVEL", logging.INFO)
    service_name = app.config.get("SERVICE_NAME", "ai-recruiter-pro")
    log_to_file = app.config.get("LOG_TO_FILE", True)
    log_file = app.config.get("LOG_FILE", "logs/app.log")

    # Initialize unified logging and correlation middleware
    try:
        from utils.unified_logging import configure_logging

        configure_logging(
            level=log_level,
            service_name=service_name,
            log_to_file=log_to_file,
            log_file=log_file,
            log_to_console=True,
        )
        logger.info("Unified logging system configured")

        from middleware.correlation_middleware import init_correlation_middleware

        init_correlation_middleware(app)
        logger.info("Correlation middleware initialized")
    except Exception as e:
        logger.warning(f"Could not initialize enhanced logging: {e!s}")


def _initialize_database_and_roles(app, skip_role_init=False):
    """Initialize database models and role definitions"""
    # Import DB from extensions to ensure it's initialized
    from extensions import db

    # Ensure Role model is created and initialized
    with app.app_context():
        # First make sure all tables exist
        db.create_all()

        # Apply Role model fixes if needed
        if not skip_role_init:
            try:
                # Import the migration function
                from migrate import apply_role_model_fix

                # Apply the role model fix
                apply_role_model_fix()

                # Initialize roles using the utility function
                from utils.initializers.roles import initialize_roles

                initialize_roles()
            except Exception as e:
                app.logger.error(f"Error initializing Role model: {e}")
        else:
            app.logger.info("Skipping role initialization as requested")


def create_app(
    config_name: str | None = None,
    skip_role_init: bool = False,
    test_config: dict[str, Any] | None = None,
) -> "Flask":
    """
    Factory function to create and configure a Flask application instance.

    Args:
        config_name: String specifying which configuration to use:
                     'development', 'testing', or 'production'
                     If None, it will be determined from environment variables.
        skip_role_init: If True, skip the role model initialization, useful for testing.
        test_config: Dictionary of test configuration values to override defaults.
                     This is useful for unit testing.

    Returns:
        Configured Flask application instance
    """
    # Late import Flask and extensions to avoid circular dependencies
    from flask import Flask, request
    from werkzeug.middleware.proxy_fix import ProxyFix

    from extensions import csrf, db, jwt, login_manager, migrate

    # Create Flask app instance
    app = Flask(__name__)

    # If config_name not provided, determine from environment
    if config_name is None:
        # Use our enhanced environment detection from config.py
        from config import get_environment_name

        config_name = get_environment_name()

    logger.info(f"Creating Flask application with config: {config_name}")

    # Apply base configuration from config object
    app.config.from_object(config[config_name])

    # Override with test config if provided
    if test_config:
        app.config.update(test_config)

    # Apply additional configuration steps from config class
    config[config_name].init_app(app)

    # Configure JWT settings (before initializing jwt extension)
    # Using the improved ConfigService for consistent environment detection
    from services.config_service import get_config

    config_service = get_config()
    config_service.get("is_replit")
    config_service.is_production()
    use_secure_cookies = app.config.get("SECURE_COOKIES", config_service.should_use_https())

    app.config.update(
        {
            "JWT_SECRET_KEY": config_service.get_jwt_secret_key(),
            "JWT_TOKEN_LOCATION": ["cookies"],
            "JWT_COOKIE_SECURE": use_secure_cookies,  # False for Replit dev, True in production
            "JWT_COOKIE_CSRF_PROTECT": True,
            "JWT_CSRF_IN_COOKIES": True,  # Store CSRF token in a cookie for easy access by client
            "JWT_ACCESS_CSRF_HEADER_NAME": "X-CSRF-TOKEN",  # Match name in guide
            "JWT_ACCESS_CSRF_COOKIE_NAME": "csrf_access_token",  # Named cookie for access token CSRF
            "JWT_REFRESH_CSRF_COOKIE_NAME": "csrf_refresh_token",  # Named cookie for refresh token CSRF
            "JWT_COOKIE_SAMESITE": "Lax",
            "JWT_SESSION_COOKIE": False,
            "JWT_ACCESS_TOKEN_EXPIRES": timedelta(minutes=30),
            "JWT_REFRESH_TOKEN_EXPIRES": timedelta(days=30),
            "JWT_ERROR_MESSAGE_KEY": "message",
            # Enhanced JWT security settings
            "JWT_CSRF_CHECK_FORM": True,  # Check for CSRF tokens in form data too
            "JWT_CSRF_METHODS": [
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            ],  # Methods that require CSRF protection
            "JWT_IDENTITY_CLAIM": "sub",  # Standard claim for user identity
            "JWT_DECODE_AUDIENCE": None,  # Audience verification - set in production
            "JWT_DECODE_LEEWAY": 10,  # Allow small clock skew (in seconds)
        }
    )

    logger.info(f"JWT configured with secure cookies: {use_secure_cookies}")

    # Configure CSRF protection settings
    app.config.update(
        {
            # Disable Flask-WTF CSRF protection in favor of our custom middleware
            # This resolves conflicts between the two CSRF systems
            "WTF_CSRF_ENABLED": False,
            # Custom CSRF middleware settings
            "CSRF_EXEMPT_PATHS": [
                "/api/public",  # Public API endpoints
                "/auth/jwt/login",  # Login endpoint that sets the token
                "/auth/jwt/csrf-token",  # CSRF token endpoint
                "/auth/jwt/refresh",  # Token refresh endpoint
                "/auth/jwt/forgot-password",  # Forgot password endpoint
                "/auth/jwt/reset-password",  # Reset password endpoint (will match all tokens)
            ],
            "CSRF_EXEMPT_API": False,  # We want to protect API routes with CSRF too
        }
    )

    # Add CSRF debugging middleware for Replit
    @app.before_request
    def log_csrf():
        """Log CSRF token presence for debugging"""
        if request.method in ["POST", "PUT", "DELETE"]:
            csrf_token = request.headers.get("X-CSRF-TOKEN") or request.headers.get("X-CSRF-Token")
            app.logger.debug(f"🔐 CSRF Token in Header: {bool(csrf_token)}")

    # Configure secret key from ConfigService
    app.secret_key = config_service.get("secret_key")

    # Add ProxyFix middleware for handling reverse proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure database with retries for connection issues
    app.config["SQLALCHEMY_DATABASE_URI"] = config_service.get("database_url")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 10},
    }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)

    # Initialize Flask-Migrate for database migrations
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    migrate.init_app(app, db, directory=migrations_dir)
    logger.info(f"Database migration system initialized with directory: {migrations_dir}")

    # Initialize unified logging system
    _initialize_logging(app)

    # Register centralized error handlers
    try:
        # First try to use the new typed error handlers
        from utils.error_handlers import register_error_handlers

        register_error_handlers(app)
        logger.info("Typed error handlers registered successfully")
    except ImportError:
        # Fall back to the old error handlers if the new ones aren't available
        from utils.error_handling import register_error_handlers

        register_error_handlers(app)
        logger.info("Legacy error handlers registered successfully")

    # Initialize database models and roles
    _initialize_database_and_roles(app, skip_role_init)

    # Import request utilities
    from utils.request_utils import is_api_request, is_htmx_request

    # Set up JWT token blocklist and callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        Check if the token is in the blocklist.
        This is called automatically by flask-jwt-extended.

        This function uses the TokenService for checking if tokens are revoked,
        centralizing all token operations in the service layer.
        """

        from services.token_service import TokenService

        jti = jwt_payload["jti"]

        # Use the token service to check if the token is revoked
        try:
            return TokenService.is_token_revoked(jti)
        except Exception as e:
            # Log the error
            app.logger.error(f"Error checking if token is revoked: {e!s}")
            # In case of error, consider token revoked (secure default)
            return True

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """
        Handle expired tokens by directing users to sign in again
        Uses request type detection to provide appropriate response formats
        """
        # Get user info for logging if available
        user_id = jwt_payload.get("sub")

        # Log the token expiration
        app.logger.info(
            f"Token expired for user {user_id}",
            extra={
                "user_id": user_id,
                "token_type": jwt_payload.get("type", "access"),
                "ip": request.remote_addr,
                "user_agent": request.user_agent.string,
            },
        )

        # Check if this is a validation endpoint first
        validation_endpoints = ["/api/v2/auth/validate", "/auth/jwt/validate", "/auth/validate"]
        if any(endpoint in request.path for endpoint in validation_endpoints):
            from flask import jsonify

            return (
                jsonify(
                    {
                        "authenticated": False,
                        "error": "AuthTokenExpired",
                        "message": "Your session has expired. Please sign in again.",
                    }
                ),
                401,
            )

        # For HTMX requests, return a redirect header
        elif is_htmx_request():
            from flask import jsonify, url_for

            response = jsonify({"status": "error", "message": "Your session has expired"})
            response.headers["HX-Redirect"] = url_for("jwt_auth.signin_page")
            return response, 401

        # For API requests, return a JSON response
        elif is_api_request():
            from flask import jsonify

            return (
                jsonify(
                    {
                        "authenticated": False,
                        "error": "AuthTokenExpired",
                        "message": "Token has expired. Please sign in again.",
                    }
                ),
                401,
            )

        # For regular requests, redirect to login page
        else:
            from flask import flash, redirect, url_for

            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for("jwt_auth.signin_page"))

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """
        Handle missing tokens by directing users to sign in
        Uses request type detection to provide appropriate response formats
        """
        # Log the unauthorized access attempt
        app.logger.warning(
            f"Unauthorized access attempt: {error_string}",
            extra={
                "ip": request.remote_addr,
                "path": request.path,
                "method": request.method,
                "user_agent": request.user_agent.string,
            },
        )

        # Check if this is a validation endpoint first
        validation_endpoints = ["/api/v2/auth/validate", "/auth/jwt/validate", "/auth/validate"]
        if any(endpoint in request.path for endpoint in validation_endpoints):
            from flask import jsonify

            return (
                jsonify(
                    {
                        "authenticated": False,
                        "error": "AuthTokenMissing",
                        "message": "No authentication token provided.",
                    }
                ),
                401,
            )

        # For HTMX requests, return a redirect header
        elif is_htmx_request():
            from flask import jsonify, url_for

            response = jsonify({"status": "error", "message": "Authentication required"})
            response.headers["HX-Redirect"] = url_for("jwt_auth.signin_page")
            return response, 401

        # For API requests, return a JSON response
        elif is_api_request():
            from flask import jsonify

            return (
                jsonify(
                    {
                        "authenticated": False,
                        "error": "AuthTokenMissing",
                        "message": "Authentication required. Please sign in.",
                    }
                ),
                401,
            )

        # For regular requests, redirect to login page
        else:
            from flask import flash, redirect, url_for

            flash("Please log in to access this page.", "warning")
            return redirect(url_for("jwt_auth.signin_page"))

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """
        Handle non-fresh token when a fresh token is required
        This is important for sensitive operations like password changes
        """
        # Get user info for logging if available
        user_id = jwt_payload.get("sub")

        # Log the fresh token requirement
        app.logger.info(
            f"Fresh token required for user {user_id}",
            extra={"user_id": user_id, "path": request.path, "method": request.method},
        )

        # For HTMX requests, return a redirect header
        if is_htmx_request():
            from flask import jsonify, url_for

            response = jsonify(
                {"status": "error", "message": "This action requires fresh authentication"}
            )
            response.headers["HX-Redirect"] = url_for("jwt_auth.signin_page")
            return response, 401

        # For API requests, return a JSON response with re-authentication directive
        elif is_api_request():
            from flask import jsonify

            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "This action requires fresh authentication",
                        "code": "fresh_token_required",
                        "action": "reauthenticate",
                    }
                ),
                401,
            )

        # For regular requests, redirect to login page with message
        else:
            from flask import flash, redirect, url_for

            flash("This action requires fresh authentication. Please log in again.", "warning")
            return redirect(url_for("jwt_auth.signin_page"))

    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_data):
        """
        Handle token verification failures for security monitoring
        This helps detect potential JWT tampering attempts
        """
        # Log the verification failure with detailed info
        app.logger.warning(
            "JWT verification failed",
            extra={
                "ip": request.remote_addr,
                "user_agent": request.user_agent.string,
                "path": request.path,
                "method": request.method,
                "headers": jwt_header,
            },
        )

        # For API requests, return JSON error
        if is_api_request():
            from flask import jsonify

            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Token verification failed",
                        "code": "token_invalid",
                    }
                ),
                401,
            )

        # For all other requests, redirect to login
        from flask import redirect, url_for

        return redirect(url_for("jwt_auth.signin_page"))

    # Set up CSRF protection middleware
    # Only use our custom CSRF middleware if Flask-WTF is disabled
    # This prevents conflicts between the two CSRF systems
    if app.config.get("WTF_CSRF_ENABLED", True) is False:

        @app.before_request
        def before_request():
            from middleware.csrf import csrf_protect

            csrf_protect()

            # Sync JWT token with Flask session
            from middleware.jwt_to_session import sync_jwt_with_session

            sync_jwt_with_session()

    else:

        @app.before_request
        def before_request():
            # Only sync JWT with session when using Flask-WTF for CSRF
            from middleware.jwt_to_session import sync_jwt_with_session

            sync_jwt_with_session()

    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Only add the following headers in production
        if app.config.get("ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    # Set up login manager with JWT auth
    login_manager.login_view = "jwt_auth.signin_page"  # Points to JWT auth blueprint's signin route
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from models import Recruiter

        try:
            return Recruiter.query.get(user_id)
        except Exception as e:
            app.logger.error(f"Error loading user: {e}")
            return None

    # Import models here to avoid circular imports
    with app.app_context():
        # Import models
        import models  # noqa

        # Create tables if they don't exist
        db.create_all()

        # Initialize admin roles only if not skipping
        if not skip_role_init:
            from utils.initializers import update_demo_password
            from utils.initializers.roles import initialize_roles

            initialize_roles()

            # Update demo account if needed
            update_demo_password(config_service.get("demo_password"))

    # Register blueprints
    register_blueprints(app)

    # Initialize templating utilities
    init_template_utilities(app)

    # Initialize asset management
    init_asset_management(app)

    # Initialize scheduler and background tasks
    init_background_tasks(app)

    # Schedule token blocklist cleanup task
    def schedule_token_cleanup():
        """Schedule a task to clean up expired tokens from the blocklist"""
        try:
            from services.token_service import TokenService

            # Clean up immediately to avoid startup with stale data
            with app.app_context():
                removed = TokenService.clean_expired_tokens()
                app.logger.info(f"Cleaned {removed} expired tokens during startup")

            # Set up a scheduled task to clean up every day
            if not app.config.get("TESTING"):
                import threading
                import time

                def cleanup_tokens_periodic():
                    """Run the token cleanup task periodically"""
                    while True:
                        try:
                            # Sleep for a day
                            time.sleep(24 * 60 * 60)  # 24 hours

                            # Clean up expired tokens
                            with app.app_context():
                                removed = TokenService.clean_expired_tokens()
                                app.logger.info(
                                    f"Cleaned {removed} expired tokens during scheduled maintenance"
                                )
                        except Exception as e:
                            app.logger.error(f"Error cleaning expired tokens: {e}")

                # Start the cleanup thread
                cleanup_thread = threading.Thread(target=cleanup_tokens_periodic, daemon=True)
                cleanup_thread.start()
                app.logger.info("Scheduled token blocklist cleanup task")
        except Exception as e:
            app.logger.error(f"Failed to schedule token cleanup: {e}")

    return app


def register_error_handlers(app):
    """
    Register custom error handlers with the Flask application.

    Args:
        app: Flask application instance
    """
    # Import the standardized response utilities if they exist
    try:
        from utils.error_handling import AuthorizationError, NotFoundError, ValidationError
        from utils.response_utils import error_response

        # Using standardized response utilities

        # 404 Not Found
        @app.errorhandler(404)
        def not_found(error):
            app.logger.warning(f"404 error: {error}")
            error_message = str(error) or "The requested resource was not found"
            return error_response(message=error_message, template="404.html", status_code=404)

        # 500 Internal Server Error
        @app.errorhandler(500)
        def internal_error(error):
            app.logger.error(f"500 error: {error}")
            return error_response(
                message="An unexpected error occurred. Our team has been notified.",
                data={"details": str(error)} if app.debug else None,
                template="500.html",
                status_code=500,
            )

        # 400 Bad Request (including CSRF validation errors)
        @app.errorhandler(400)
        def bad_request(error):
            app.logger.warning(f"400 error: {error}")

            # For CSRF errors, we need to refresh the token
            error_message = str(error) or "Bad Request - Invalid data or CSRF validation failed"

            response = error_response(message=error_message, template="400.html", status_code=400)

            # If this is a CSRF error, add a fresh token
            if "CSRF" in error_message:
                try:
                    from middleware.csrf import generate_csrf_token

                    csrf_token = generate_csrf_token()
                    # Unpack the tuple returned by error_response
                    resp, status_code = response
                    # Now we can set the cookie on the actual response object
                    resp.set_cookie("csrf_token", csrf_token, httponly=False, samesite="Lax")
                    # Return the modified response with status code
                    return resp, status_code
                except ImportError:
                    app.logger.warning(
                        "Could not generate CSRF token: middleware.csrf not available"
                    )

            return response

        # 403 Forbidden (including CSRF errors)
        @app.errorhandler(403)
        def forbidden(error):
            app.logger.warning(f"403 error: {error}")

            error_message = (
                str(error) or "Forbidden - You don't have permission to access this resource"
            )

            # For CSRF errors, we should redirect to login page
            redirect_url = None
            if "CSRF" in error_message:
                try:
                    from flask import url_for

                    redirect_url = url_for("jwt_auth.signin_page")
                except:
                    redirect_url = "/login"  # Fallback if url_for fails

                # Create response with redirect
                response = error_response(
                    message=error_message,
                    template="403.html",
                    status_code=403,
                    redirect_url=redirect_url,
                )

                # Add a fresh token
                try:
                    from middleware.csrf import generate_csrf_token

                    csrf_token = generate_csrf_token()
                    # Unpack the tuple returned by error_response
                    resp, status_code = response
                    # Now we can set the cookie on the actual response object
                    resp.set_cookie("csrf_token", csrf_token, httponly=False, samesite="Lax")
                    # Return the modified response with status code
                    return resp, status_code
                except ImportError:
                    app.logger.warning(
                        "Could not generate CSRF token: middleware.csrf not available"
                    )

                return response

            # Standard 403 response
            return error_response(message=error_message, template="403.html", status_code=403)

        # Custom ValidationError handler
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            app.logger.warning(f"Validation error: {error}")
            return error_response(
                message=str(error),
                status_code=400,
                data={"details": error.details} if hasattr(error, "details") else None,
            )

        # Custom AuthorizationError handler
        @app.errorhandler(AuthorizationError)
        def handle_authorization_error(error):
            app.logger.warning(f"Authorization error: {error}")
            return error_response(message=str(error), status_code=403)

        # Custom NotFoundError handler
        @app.errorhandler(NotFoundError)
        def handle_not_found_error(error):
            app.logger.warning(f"Not found error: {error}")
            return error_response(message=str(error), status_code=404)

    except ImportError:
        # Fall back to legacy implementation if the new utilities aren't available
        app.logger.warning(
            "Using legacy error handlers - standardized response utilities not found"
        )

        # 404 Not Found
        @app.errorhandler(404)
        def not_found_legacy(error):
            from flask import render_template

            return render_template("404.html"), 404

        # 500 Internal Server Error
        @app.errorhandler(500)
        def internal_error_legacy(error):
            from flask import render_template

            app.logger.error(f"500 error: {error}")
            return render_template("500.html"), 500

        # 400 Bad Request (including CSRF validation errors)
        @app.errorhandler(400)
        def bad_request_legacy(error):
            app.logger.warning(f"400 error: {error}")

            # Import request utilities
            from utils.request_utils import is_api_request, is_htmx_request

            # Check if this is an HTMX request
            if is_htmx_request():
                response = jsonify(
                    {
                        "status": "error",
                        "message": str(error)
                        or "Bad Request - Invalid data or CSRF validation failed",
                    }
                )
                # Generate a fresh CSRF token
                from middleware.csrf import generate_csrf_token

                csrf_token = generate_csrf_token()
                response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="Lax")
                return response, 400

            # Check if this is an API request
            elif is_api_request():
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(error)
                            or "Bad Request - Invalid data or CSRF validation failed",
                        }
                    ),
                    400,
                )

            # For regular requests
            return (
                render_template("400.html", error=str(error) or "Bad Request - Invalid data"),
                400,
            )

        # 403 Forbidden (including CSRF errors)
        @app.errorhandler(403)
        def forbidden_legacy(error):
            app.logger.warning(f"403 error: {error}")

            # Import request utilities
            from flask import jsonify, render_template, url_for

            from utils.request_utils import is_api_request, is_htmx_request

            # Check if this is an HTMX request
            if is_htmx_request():
                response = jsonify(
                    {
                        "status": "error",
                        "message": str(error) or "Forbidden - CSRF validation failed",
                    }
                )
                # Generate a fresh CSRF token
                from middleware.csrf import generate_csrf_token

                csrf_token = generate_csrf_token()
                response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="Lax")
                response.headers["HX-Redirect"] = url_for("jwt_auth.signin_page")
                return response, 403

            # Check if this is an API request
            elif is_api_request():
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(error) or "Forbidden - CSRF validation failed",
                        }
                    ),
                    403,
                )

            # For regular requests
            return render_template("403.html", error=str(error) or "CSRF validation failed"), 403

    # Handle unauthorized HTMX requests
    @app.after_request
    def redirect_unauthorized_htmx(response):
        """
        Handle unauthorized HTMX requests by setting the HX-Redirect header to the login page.
        HTMX will automatically redirect to this URL when it receives this header.
        """
        # Import request utilities
        from utils.request_utils import is_htmx_request

        if response.status_code == 401 and is_htmx_request():
            # Use the JWT auth blueprint's signin route
            response.headers["HX-Redirect"] = url_for("jwt_auth.signin_page")
        return response


def register_blueprints(app):
    """
    Register blueprints with the Flask application.

    Args:
        app: Flask application instance
    """
    # Use the centralized blueprint registration
    from routes import register_all_blueprints

    register_all_blueprints(app)

    # Register direct routes to ensure application is accessible

    # Root route with fallback HTML
    @app.route("/")
    def index():
        """Serve a direct HTML page to avoid redirection issues"""
        app.logger.info("Root route accessed")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Recruiter Pro</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2563eb; }
                .btn { 
                    display: inline-block; 
                    background: #2563eb; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    font-weight: bold;
                }
                .btn:hover { background: #1e40af; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to AI Recruiter Pro</h1>
                <p>An advanced AI-powered recruitment platform that leverages intelligent microservices 
                to streamline candidate management and optimize hiring workflows.</p>
                <p>
                    <a href="/auth/jwt/signin" class="btn">Sign In</a>
                </p>
            </div>
        </body>
        </html>
        """

    # Add a signin redirect for better user experience 
    @app.route("/signin")
    def signin_redirect():
        """Redirect to the JWT signin page for better user experience"""
        from flask import redirect, url_for
        app.logger.info("Signin redirect accessed")
        return redirect(url_for("jwt_auth.signin_page"))
        
    # Add a simple health check that doesn't use jsonify to avoid import issues
    @app.route("/health")
    def health_check():
        """Simplified health check that works regardless of application state"""
        app.logger.info("Health check endpoint accessed")
        return "OK", 200

    # Add a detailed JSON health check
    @app.route("/api/health")
    def api_health_check():
        """Detailed health check endpoint to verify app is running"""
        app.logger.info("API health check endpoint accessed")
        try:
            from datetime import datetime

            from flask import jsonify

            response = {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "version": os.environ.get("APP_VERSION", "development"),
                "environment": (
                    "production" if app.config.get("ENV") == "production" else "development"
                ),
            }
            return jsonify(response)
        except Exception as e:
            app.logger.error(f"Error in API health check: {e!s}")
            return "Application running but JSON response unavailable", 200


def init_template_utilities(app):
    """
    Initialize template filters and global variables for the application.

    Args:
        app: Flask application instance
    """

    # Add template filters
    @app.template_filter("datetimeformat")
    def datetimeformat(value, format="%b %d, %Y"):
        """Convert a datetime to a different format."""
        if value is None:
            return ""
        return value.strftime(format)

    # Add asset info for templates
    @app.context_processor
    def inject_asset_info():
        """Inject asset information into all templates"""
        try:
            from utils.assets_new import get_asset_url

            return {"asset_url": get_asset_url}
        except ImportError:
            app.logger.warning("Asset resolution utilities not found")
            return {}

    # Add smart URL helper that handles blueprint prefixes
    @app.context_processor
    def inject_url_helper():
        """Inject enhanced URL helper for blueprint management"""
        try:
            from utils.url_helpers import url_for as smart_url_for

            return {"smart_url": smart_url_for}
        except ImportError:
            app.logger.warning("URL helper utilities not found")
            return {}

    # Add page type injector
    @app.context_processor
    def inject_page_type():
        """Inject page type based on the current route"""
        # Import request at the function level to avoid circular imports
        from flask import request as flask_request
        
        try:
            if hasattr(flask_request, "endpoint") and flask_request.endpoint:
                route = flask_request.endpoint.split(".")[-1] if "." in flask_request.endpoint else flask_request.endpoint
                return {"page_type": route}
        except Exception as e:
            app.logger.error(f"Error in page_type injector: {e}")
        
        return {"page_type": "unknown"}

    # Add current user injector
    @app.context_processor
    def inject_current_user():
        """Inject current_user into all templates based on token"""
        from flask_login import current_user

        return {"current_user": current_user}

    # Try to load comprehensive template helpers if available
    try:
        from utils.template_helpers import register_template_helpers

        register_template_helpers(app)
        app.logger.info("Comprehensive template helpers registered")
    except ImportError:
        app.logger.info("Comprehensive template helpers not available")


def init_asset_management(app):
    """
    Initialize asset management for the application.

    Args:
        app: Flask application instance
    """
    try:
        from utils.assets_new import load_assets

        load_assets()
        app.logger.info("Using new asset resolution system")
    except (ImportError, Exception) as e:
        app.logger.warning(f"Could not initialize asset management: {e}")


def init_background_tasks(app):
    """
    Initialize background tasks and schedulers for the application.

    Args:
        app: Flask application instance
    """
    # We'll move the implementation of scheduler initialization here
    # As we refactor app.py

    # For now, we'll call the existing code
    with app.app_context():
        try:
            # Initialize the DI container
            try:
                setup_container()
                app.logger.info("Dependency Injection container initialized successfully")
            except Exception as e:
                app.logger.error(f"Error initializing DI container: {e}")

            # Check if DISABLE_SCHEDULER is set
            if os.environ.get("DISABLE_SCHEDULER", "").lower() == "true":
                app.logger.info("Scheduler disabled via environment variable")
                return

            # Run job expiration check
            app.logger.info("Running scheduled job expiration check")
            from utils.job_expiration_service import check_for_expired_jobs, check_for_expiring_jobs

            expired_count = check_for_expired_jobs()
            expiring_count = check_for_expiring_jobs()
            app.logger.info(
                f"Scheduled task completed: {expired_count} jobs expired, {expiring_count} jobs marked for notification"
            )

            # Initialize the resume processor with middleware to properly handle application context
            app.logger.info("Resume processor will be initialized on first request")

            # Set up a resume processor initializer middleware
            from utils.resume_processor import init_processor, start_background_thread

            # Create a flag to track initialization status
            resume_processor_started = False

            # Add middleware to initialize the processor on first request
            @app.before_request
            def initialize_resume_processor():
                nonlocal resume_processor_started
                if not resume_processor_started:
                    app.logger.info("First request detected, initializing resume processor")
                    init_processor(app)
                    # Start the background thread with proper app context
                    start_background_thread()
                    resume_processor_started = True

            # Run schema validation if enabled in config
            if app.config.get("VALIDATE_SCHEMA_ON_STARTUP", False):
                app.logger.info("Running database schema validation...")
                try:
                    from utils.schema_validator import schema_consistency_check

                    schema_valid = schema_consistency_check()
                    if schema_valid:
                        app.logger.info("Schema validation passed for all models")
                    else:
                        app.logger.warning(
                            "Schema validation found inconsistencies. See logs for details."
                        )
                except Exception as e:
                    app.logger.error(f"Error running schema validation: {e!s}")

        except Exception as e:
            app.logger.error(f"Error initializing background tasks: {e}")
