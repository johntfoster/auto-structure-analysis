"""Pytest fixtures and configuration."""

import io
import numpy as np
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from PIL import Image

from app.main import app
from app.models.schemas import StructuralModel, Node, Member, Support, Load


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Asynchronous test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_image():
    """Generate a simple test image."""
    # Create a 500x500 white image
    img = Image.new('RGB', (500, 500), color='white')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes


@pytest.fixture
def sample_image_array():
    """Generate a test image as numpy array."""
    # Create white image (BGR format)
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    return img


@pytest.fixture
def simple_truss_model():
    """Simple 3-node triangle truss model."""
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=1000.0, y=0.0),
        Node(id="N3", x=500.0, y=866.0),  # ~60° triangle
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),
        Member(id="M2", start_node="N2", end_node="N3", material="steel"),
        Member(id="M3", start_node="N3", end_node="N1", material="steel"),
    ]
    
    supports = [
        Support(node_id="N1", type="pin"),
        Support(node_id="N2", type="roller"),
    ]
    
    return StructuralModel(nodes=nodes, members=members, supports=supports)


@pytest.fixture
def simple_loads():
    """Simple vertical load at apex."""
    return [
        Load(node_id="N3", fx=0.0, fy=-1000.0)  # 1kN downward
    ]
