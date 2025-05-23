"""Package initialization for the FastAPI application.

This module imports and exposes key components-intro required for API routing,
including the main FastAPI router and metadata tags used for API documentation.

Exports:
    - `router`: The main FastAPI APIRouter instance containing all route definitions.
    - `TAG_METADATA`: Metadata describing API tags for better documentation.

These components-intro can be imported directly from the package for use in the
application.
"""

# Package Library
from chaturai.admin.routers import TAG_METADATA, router

__all__ = ["router", "TAG_METADATA"]
