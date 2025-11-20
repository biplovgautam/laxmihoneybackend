# Laxmi Honey Backend

A FastAPI-based backend service for the Laxmi Honey application.

## Project Structure

```
laxmihoneybackend/
├── app/
│   ├── __init__.py
│   ├── check.py
│   ├── llmwrapper.py
│   ├── laxmihoneyapp/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── mindshippingapp/
│       ├── __init__.py
│       └── routes.py
├── main.py
├── requirements.txt
├── dockerfile
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

### Service Overview

- **`/api1` – Laxmi Honey backend**
  - `GET /api1/health` – Service-specific health check
  - `POST /api1/llm` – Proxy to GroqLLM (requires `GROQ_LLM_API` in `.env`)
- **`/api2` – MindShipping backend**
  - `GET /api2/health` – Service-specific health check
  - `GET /api2/info` – Placeholder info endpoint

Both services sit behind the same FastAPI instance (`main.py`). You can extend each folder with additional routers, models, and services as needed, keeping logic isolated per backend.

### CORS configuration

Allow only trusted frontends by setting a single environment variable before starting the server:

```
ALLOWED_ORIGINS="http://localhost:3000,https://laxmibeekeeping.com.np,https://www.laxmibeekeeping.com.np,https://www.mindshipping.tech"
```

If `ALLOWED_ORIGINS` is undefined, the app falls back to the list shown above (which already includes `https://www.mindshipping.tech`).

### Multi-backend routing

Routers are registered dynamically from the `SERVICE_CONFIG` list in `main.py`. Each entry defines:

- `name`: human-friendly identifier used in logs and the `/health` summary
- `module`: Python import path to the backend package (e.g., `app.laxmihoneyapp`)
- `router_name`: router object exposed from that package (e.g., `laxmihoney_router`)
- `prefix`: URL prefix (e.g., `/api1`)
- `tags`: tags shown in the generated OpenAPI docs
- `enabled`: default boolean toggle

To temporarily disable/enable a subset of services without editing code, set the `ENABLED_SERVICES` environment variable before starting Uvicorn:

```bash
export ENABLED_SERVICES=laxmihoney  # loads only /api1
uvicorn main:app --reload
```

This makes each backend folder portable—copy `app/mindshippingapp` into another project, add one entry to `SERVICE_CONFIG`, and it will mount automatically under its prefix.

### Frontend API base URLs

Point the frontend(s) to these base paths so requests reach the intended backend:

- **Laxmi Honey UI:** `https://<your-domain>/api1/*` (e.g., `https://laxmibeekeeping.com.np/api1/llm`)
- **MindShipping UI:** `https://<your-domain>/api2/*`

When deploying Koyeb or another host, expose a single FastAPI app and route frontend requests to the relevant prefix.

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
