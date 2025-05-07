# API Documentation

AI Recruiter Pro offers a comprehensive API for integrating with enterprise Applicant Tracking Systems (ATS) and other third-party services.

## Authentication

All API endpoints require authentication using JWT tokens.

### Getting an API Token

```
POST /api/v2/auth/token
```

**Request Body:**
```json
{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header of all requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5...
```

## Core Endpoints

### Candidates

#### List Candidates

```
GET /api/v2/candidates
```

**Query Parameters:**
- `page` (int, optional): Page number for pagination
- `per_page` (int, optional): Items per page (default: 20)
- `query` (string, optional): Search query
- `skills` (string, optional): Comma-separated list of skills to filter by

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "Flask", "React"],
      "experience_years": 5,
      "created_at": "2025-04-15T14:30:45Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

#### Get Candidate

```
GET /api/v2/candidates/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "summary": "Experienced software developer...",
  "skills": ["Python", "Flask", "React"],
  "experience": [
    {
      "title": "Senior Developer",
      "company": "Tech Corp",
      "start_date": "2020-01",
      "end_date": "2025-04",
      "description": "Led development team..."
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Science",
      "institution": "University of Technology",
      "field": "Computer Science",
      "graduation_year": 2018
    }
  ],
  "resume_url": "/api/v2/candidates/1/resume",
  "created_at": "2025-04-15T14:30:45Z",
  "updated_at": "2025-04-15T14:30:45Z"
}
```

#### Create Candidate

```
POST /api/v2/candidates
```

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+1987654321",
  "summary": "Full-stack developer...",
  "skills": ["JavaScript", "Node.js", "Express"],
  "experience": [
    {
      "title": "Developer",
      "company": "Web Solutions",
      "start_date": "2019-05",
      "end_date": "2025-03",
      "description": "Developed web applications..."
    }
  ],
  "education": [
    {
      "degree": "Master of Science",
      "institution": "Tech University",
      "field": "Software Engineering",
      "graduation_year": 2019
    }
  ]
}
```

### Jobs

#### List Jobs

```
GET /api/v2/jobs
```

**Query Parameters:**
- `page` (int, optional): Page number for pagination
- `per_page` (int, optional): Items per page (default: 20)
- `query` (string, optional): Search query
- `status` (string, optional): Filter by status (open, closed, draft)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Senior Backend Developer",
      "company": "Tech Solutions Inc.",
      "location": "Remote",
      "status": "open",
      "created_at": "2025-04-10T09:15:30Z"
    }
  ],
  "total": 28,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

#### Get Job

```
GET /api/v2/jobs/{id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Senior Backend Developer",
  "company": "Tech Solutions Inc.",
  "department": "Engineering",
  "location": "Remote",
  "description": "We are looking for an experienced backend developer...",
  "requirements": [
    "5+ years experience with Python",
    "Experience with Flask or Django",
    "Database design experience"
  ],
  "skills": ["Python", "Flask", "PostgreSQL", "Docker"],
  "salary_range": {
    "min": 90000,
    "max": 120000,
    "currency": "USD"
  },
  "status": "open",
  "created_at": "2025-04-10T09:15:30Z",
  "updated_at": "2025-04-12T11:22:15Z"
}
```

### Matching

#### Get Matches for Job

```
GET /api/v2/jobs/{job_id}/matches
```

**Query Parameters:**
- `page` (int, optional): Page number for pagination
- `per_page` (int, optional): Items per page (default: 20)
- `min_score` (float, optional): Minimum match score (0-100)

**Response:**
```json
{
  "items": [
    {
      "candidate_id": 15,
      "candidate_name": "Alice Johnson",
      "match_score": 85.7,
      "matching_skills": ["Python", "Flask", "PostgreSQL"],
      "missing_skills": ["Docker"],
      "candidate_url": "/api/v2/candidates/15"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

#### Get Matches for Candidate

```
GET /api/v2/candidates/{candidate_id}/matches
```

**Query Parameters:**
- `page` (int, optional): Page number for pagination
- `per_page` (int, optional): Items per page (default: 20)
- `min_score` (float, optional): Minimum match score (0-100)
- `status` (string, optional): Filter by job status (open, closed, draft)

**Response:**
```json
{
  "items": [
    {
      "job_id": 3,
      "job_title": "Backend Developer",
      "company": "Tech Solutions Inc.",
      "match_score": 78.3,
      "matching_skills": ["Python", "PostgreSQL"],
      "missing_skills": ["Flask", "Docker"],
      "job_url": "/api/v2/jobs/3"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

## Error Handling

All errors return an appropriate HTTP status code and a JSON response with the following structure:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "A detailed error message",
    "details": {} 
  }
}
```

Common error codes:
- `unauthorized`: Authentication required or failed
- `forbidden`: Insufficient permissions
- `not_found`: Resource not found
- `invalid_request`: Request validation failed
- `rate_limited`: API rate limit exceeded

## Rate Limiting

API requests are rate-limited to ensure fair usage. Current limits:
- 60 requests per minute for standard users
- 120 requests per minute for enterprise users

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1617278400
```

## Versioning

The API follows semantic versioning and is currently at v2. All v1 endpoints are maintained for backward compatibility but may be deprecated in future releases.