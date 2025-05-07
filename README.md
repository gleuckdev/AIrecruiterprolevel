# AI Recruiter Pro

AI Recruiter Pro is an advanced AI-powered professional recruitment and career development platform leveraging intelligent middleware for talent matching and professional growth.

## Features

- AI-powered resume parsing and analysis
- Smart candidate-to-job matching algorithms
- Collaborative recruiting workflows
- Role-based access control
- Enterprise ATS integration
- Comprehensive API for third-party integrations

## Tech Stack

- **Backend**: Flask microservices with SQLAlchemy ORM
- **Frontend**: Alpine.js reactive components with HTMX for dynamic updates
- **Authentication**: JWT-based with HTTP-only cookies
- **Database**: PostgreSQL with comprehensive data models
- **Architecture**: Repository pattern with dependency injection
- **UI**: Tailwind CSS with semantic theming

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js 16+ (for frontend build tools)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-recruiter-pro.git
cd ai-recruiter-pro
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database
```bash
flask db upgrade
```

6. Add sample data (optional)
```bash
python scripts/add_sample_data.py
```

7. Run the application
```bash
python main.py
# or
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Documentation

- [URL Reference Guide](URL_REFERENCE_GUIDE.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the Polyform Noncommercial License 1.0.0 - see the [LICENSE](LICENSE) file for details.

This license permits use for noncommercial purposes only. For commercial use, please see our [Commercial Licensing](COMMERCIAL_LICENSING.md) options or contact: puneet@gleuck.com

## Acknowledgments

- Special thanks to all contributors
- Inspired by modern recruitment challenges and AI capabilities