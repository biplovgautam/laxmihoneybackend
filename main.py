import os

from importlib import import_module
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.check import Check

app = FastAPI()

# Configure CORS - allows frontend to access the API
origins = [
    "http://localhost:3000",          # Local development
    "https://laxmibeekeeping.com.np", # Production frontend
    "https://www.laxmibeekeeping.com.np", # Production frontend with www
]

# If you have a specific frontend URL in environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins or ["*"] for all (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


SERVICE_CONFIG = [
    {
        "name": "laxmihoney",
        "module": "app.laxmihoneyapp",
        "router_name": "laxmihoney_router",
        "prefix": "/api1",
        "tags": ["laxmihoney"],
        "enabled": True,
    },
    {
        "name": "mindshipping",
        "module": "app.mindshippingapp",
        "router_name": "mindshipping_router",
        "prefix": "/api2",
        "tags": ["mindshipping"],
        "enabled": True,
    },
]


def _resolve_enabled_services(config: List[dict]) -> List[str]:
    """Enable/disable services based on ENABLED_SERVICES env var."""

    enabled_env = os.getenv("ENABLED_SERVICES")
    if not enabled_env:
        return [service["name"] for service in config if service.get("enabled", True)]

    requested = {service.strip().lower() for service in enabled_env.split(",") if service.strip()}
    active = []
    for service in config:
        if service["name"].lower() in requested:
            service["enabled"] = True
            active.append(service["name"])
        else:
            service["enabled"] = False
    return active


registered_services: List[str] = []
active_services = _resolve_enabled_services(SERVICE_CONFIG)

for service in SERVICE_CONFIG:
    if not service.get("enabled", True):
        continue
    try:
        module = import_module(service["module"])
        router = getattr(module, service["router_name"])
        app.include_router(router, prefix=service["prefix"], tags=service["tags"])
        registered_services.append(service["name"])
    except Exception as exc:
        print(
            f"Warning: Failed to load service '{service['name']}' from {service['module']} - {exc}"
        )


@app.get("/")
def main():
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check():
    checker = Check()
    return {
        "status": checker.checking(),
        "services": registered_services or active_services,
    }