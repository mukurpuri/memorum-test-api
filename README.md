# Memorum Test API

A simple Python REST API for testing Memorum's decision memory capture.

## What is this?

This is a minimal API service used to demonstrate how Memorum captures architectural decisions from pull requests.

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{id}` - Get user by ID

## Architecture

- `app/` - Application code
  - `main.py` - FastAPI application entry
  - `models.py` - Data models
  - `routes/` - API route handlers
  - `db/` - Database layer
- `tests/` - Test suite

## License

MIT
