# Laxmi Honey Backend

A FastAPI-based backend service for the Laxmi Honey application.

## Project Structure

```
laxmihoneybackend/
├── app/
│   ├── __init__.py
│   └── check.py          # Health check module
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── dockerfile            # Docker configuration
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/biplovgautam/laxmihoneybackend.git
cd laxmihoneybackend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Setup

Build the Docker image:
```bash
docker build -t laxmihoneybackend .
```

## Running the Application

### Local Development

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker

Run the container:
```bash
docker run -p 8000:8000 laxmihoneybackend
```

## API Endpoints

### GET /
Returns a welcome message.

**Response:**
```json
{
  "message": "Hello, World!"
}
```

### GET /health
Health check endpoint to verify service status.

**Response:**
```json
{
  "status": "connected"
}
```

## API Documentation

FastAPI provides automatic interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Adding New Endpoints

1. Define routes in `main.py` or create new modules in the `app/` directory
2. Import and register routes in `main.py`
3. Test endpoints using the interactive documentation

### Project Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications

## License

This project is proprietary and confidential.
