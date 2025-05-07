# Architecture

## Overview

AI Recruiter Pro is a Flask-based web application designed to match candidates with job opportunities using AI-powered analysis. The system uses natural language processing to extract information from resumes, analyze job descriptions, and create optimal matches between candidates and positions.

The application follows a clean architecture pattern with distinct layers for presentation, business logic, data access, and infrastructure. It employs a comprehensive service-oriented design and dependency injection to ensure modularity and testability.

## System Architecture

### Core Architecture Patterns

1. **Clean Architecture**: The application separates concerns into domain, application, interface, and infrastructure layers, allowing for better maintainability and testability.

2. **Repository Pattern**: Data access is abstracted through repositories, providing a separation between business logic and data storage mechanisms.

3. **Dependency Injection**: Services and repositories are instantiated and configured through a DI container, reducing direct dependencies between components.

4. **Service Layer**: Business logic is encapsulated in service classes that handle specific domains of functionality.

5. **Blueprint-Based Routes**: The Flask application is organized using blueprints for modular routing and separation of concerns.

## Key Components

### Backend Components

1. **Application Factory**
   - Located in `app_factory.py`
   - Creates and configures the Flask application with appropriate middleware, error handlers, and route registrations
   - Supports different environment configurations (development, testing, production)

2. **Service Layer**
   - Implements core business logic in service classes
   - Services include:
     - `ResumeProcessingService`: Handles resume parsing and candidate data extraction
     - `JobMatchingService`: Implements the matching algorithm between candidates and jobs
     - `OpenAIService`: Handles integration with OpenAI's API for AI-powered analysis
     - `FeatureFlagService`: Manages feature flags for controlled feature rollout
     - `NotificationService`: Handles user notifications
   
3. **Data Access Layer**
   - Implements the repository pattern for data access
   - Uses SQLAlchemy ORM for database operations
   - Main repositories include:
     - `CandidateRepository`: Manages candidate data
     - `JobRepository`: Manages job posting data
     - `UserRepository`: Handles user account data
     - `MatchRepository`: Stores and retrieves match results

4. **Authentication System**
   - Uses JWT (JSON Web Tokens) for authentication
   - Implements token-based authentication with HTTP-only cookies
   - Includes CSRF protection for enhanced security
   - Provides role-based access control

5. **LLM Integration**
   - Abstracts LLM (Large Language Model) providers behind common interfaces
   - Supports multiple providers (primarily OpenAI)
   - Implements fallback mechanisms for API key rotation and error recovery

### Frontend Components

1. **Template Engine**
   - Uses Flask's Jinja2 template engine
   - Organizes templates in a modular structure
   - Includes layouts, partials, and page templates

2. **JavaScript Framework**
   - Uses Alpine.js for reactive UI components
   - Integrates HTMX for AJAX functionality without complex JS frameworks
   - Implements a store-based state management approach

3. **CSS Framework**
   - Uses a custom CSS framework based on Volt Dashboard
   - Implements responsive design for mobile compatibility

### Database Schema

The application uses a SQLAlchemy ORM with models organized into domain-specific modules:

1. **User Models**
   - `Recruiter`: Users who can access the system
   - `Role`: Role-based access control definitions
   - `Permission`: Granular permissions for system features
   - `Session`: User session tracking

2. **Candidate Models**
   - `Candidate`: Core candidate entity with resume data
   - `CandidateSkill`: Many-to-many relationship to skills
   - `CandidateRating`: Recruiter ratings for candidates

3. **Job Models**
   - `Job`: Job posting details
   - `JobSkill`: Required skills for jobs
   - `JobToken`: Semantic tokens extracted from job descriptions

4. **Matching Models**
   - `CandidateJobMatch`: Records match scores between candidates and jobs
   - `MatchDetail`: Detailed scoring breakdown for matches

## Data Flow

### Resume Processing Flow

1. User uploads a resume through the web interface
2. The resume is temporarily stored and passed to the ResumeProcessingService
3. The service extracts text content from the resume (PDF, DOCX, etc.)
4. The extracted text is analyzed using NLP techniques and/or AI models to identify:
   - Candidate information (name, contact details)
   - Skills and experience
   - Education background
5. The extracted information is stored in the database
6. The candidate is matched against existing job postings
7. Results are returned to the user interface

### Job Posting Flow

1. Recruiter creates a new job posting with requirements
2. The job description is analyzed to extract key requirements and skills
3. The system checks for potential bias in the job description
4. The job posting is stored in the database
5. Existing candidates are automatically matched against the new posting
6. The recruiter can view matching candidates ranked by match quality

### Matching Algorithm

The matching system uses a hybrid approach combining:

1. **Embedding-based matching**: Using vector similarity between resume and job description embeddings (60% weight)
2. **Skills-based matching**: Direct comparison of candidate skills and job requirements (40% weight)

This approach provides both semantic understanding and explicit skill matching.

## External Dependencies

### AI/ML Services

1. **OpenAI API**
   - Used for text analysis and embedding generation
   - Primary model for resume parsing and job description analysis
   - Implemented with fallback mechanisms for reliability

2. **Anthropic API (Claude models)**
   - Alternative LLM provider for certain analysis tasks
   - Used as a fallback when OpenAI is unavailable

### Database

- PostgreSQL database for production environments
- SQLAlchemy ORM for database interactions
- Alembic for database migrations

### Testing Tools

- Pytest for unit and integration testing
- Coverage reporting for test coverage analysis
- Pre-commit hooks for code quality checks

## Deployment Strategy

The application is designed to run in multiple environments:

### Development Environment

- Local development with Flask development server
- Environment variable configuration via .env files
- Debug features enabled

### Testing Environment

- In-memory or isolated databases for testing
- Mocked external services

### Production Environment

1. **Replit Deployment**
   - Configured to run in Replit environment
   - Uses Replit database
   - Runs with Gunicorn WSGI server
   - Automatically detects Replit environment

2. **Other Cloud Environments**
   - Support for deployment to Render, Heroku, AWS, GCP, or Azure
   - Environment detection for automatic configuration
   - Enhanced security settings for production (HTTPS, secure cookies)
   - Background processing with Celery (or ThreadPoolExecutor fallback in Replit)

### Environment-Specific Configurations

- Different configuration profiles based on environment detection
- Automatic HTTPS and cookie security settings based on platform
- Feature flags for controlled feature rollout across environments