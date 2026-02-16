"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, analysis

# Create FastAPI app
app = FastAPI(
    title="Auto Structure Analysis API",
    description="Automated structural analysis using computer vision and FEA",
    version="0.1.0"
)

# Configure CORS (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Auto Structure Analysis API",
        "version": "0.1.0",
        "docs": "/docs"
    }
