# AI Recruiter Pro Setup Guide

This guide provides detailed setup instructions for AI Recruiter Pro.

## Prerequisites

- Python 3.8+ installed
- PostgreSQL 12+ installed and running
- Node.js 16+ installed (for frontend asset compilation)

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ai-recruiter-pro.git
cd ai-recruiter-pro
```

## Step 2: Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
# Particularly important:
# - DATABASE_URL
# - SECRET_KEY
# - SESSION_SECRET
# - OPENAI_API_KEY (if using OpenAI features)
```

Make sure your database URL is formatted correctly:
```
DATABASE_URL=postgresql://username:password@localhost:5432/ai_recruiter_pro
```

## Step 5: Initialize Database

```bash
# Create database (if not using existing one)
createdb ai_recruiter_pro

# Apply migrations
flask db upgrade
```

## Step 6: Add Sample Data (Optional)

```bash
# Add demo user and sample data
python scripts/add_demo_user.py
python scripts/add_sample_job.py
python scripts/add_sample_candidates.py
```

## Step 7: Run the Application

### Development Mode

```bash
python main.py
```

### Production Mode

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

## Step 8: Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## Configuration Options

### Database Configuration

For production deployments, it's recommended to set up a dedicated PostgreSQL database with proper authentication.

### Authentication Setup

By default, the application creates a demo admin user:
- Email: admin@example.com
- Password: password123

Change these credentials immediately in a production environment.

### LLM API Keys

The system supports the following LLM providers:
- OpenAI (GPT models)
- Anthropic (Claude models)

Add your API keys to the .env file to enable AI features.

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:
1. Verify that PostgreSQL is running
2. Check the DATABASE_URL format in your .env file
3. Ensure the database user has proper permissions

### Environment Setup

For Windows users, you may need to install additional dependencies:
```bash
pip install python-magic-bin
```

### Missing Frontend Assets

If frontend assets are not loading correctly:
1. Check that static files are properly generated
2. Verify that the application has proper permissions to access static files

## Next Steps

- Explore the [URL Reference Guide](URL_REFERENCE_GUIDE.md) for available endpoints
- Review the [Contributing Guide](CONTRIBUTING.md) to learn how to contribute
- Join our community discussions on GitHub Issues