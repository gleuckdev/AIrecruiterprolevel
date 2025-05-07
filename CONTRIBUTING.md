# Contributing to AI Recruiter Pro

Thank you for considering contributing to AI Recruiter Pro! This document outlines the process for contributing to this project.

## License Notice

By contributing to this project, you agree that your contributions will be licensed under the project's [Polyform Noncommercial License 1.0.0](LICENSE). Please note that this license restricts commercial use without explicit permission.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and update with your configuration
6. Run the application: `python main.py`

## Code Style

Please follow the PEP 8 style guide for Python code. We use Black for code formatting and Flake8 for linting.

## Testing

Before submitting a PR, please run tests to ensure your changes don't break existing functionality:

```bash
pytest
```

## Documentation

Please update documentation as needed to reflect your changes.

## Pull Request Process

1. Ensure your code follows our style guidelines
2. Update documentation as necessary
3. Include tests for new functionality
4. Ensure all tests pass
5. Your PR will be reviewed by maintainers, who may request changes

Thank you for your contributions!