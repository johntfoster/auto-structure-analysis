"""Tests for structure detector service."""

from app.services.structure_detector import detect_structure


def test_detect_structure_returns_valid_model(sample_image_array):
    """Test that structure detection returns a valid model."""
    scale_factor = 1.0
    model = detect_structure(sample_image_array, scale_factor)
    
    # Verify model has required components
    assert len(model.nodes) > 0
    assert len(model.members) > 0
    assert len(model.supports) > 0


def test_detect_structure_nodes(sample_image_array):
    """Test that detected nodes have valid properties."""
    scale_factor = 1.0
    model = detect_structure(sample_image_array, scale_factor)
    
    for node in model.nodes:
        assert node.id is not None
        assert isinstance(node.x, float)
        assert isinstance(node.y, float)
        assert node.x >= 0
        assert node.y >= 0


def test_detect_structure_members(sample_image_array):
    """Test that detected members reference valid nodes."""
    scale_factor = 1.0
    model = detect_structure(sample_image_array, scale_factor)
    
    node_ids = {node.id for node in model.nodes}
    
    for member in model.members:
        assert member.id is not None
        assert member.start_node in node_ids
        assert member.end_node in node_ids
        assert member.material is not None


def test_detect_structure_supports(sample_image_array):
    """Test that supports reference valid nodes and have valid types."""
    scale_factor = 1.0
    model = detect_structure(sample_image_array, scale_factor)
    
    node_ids = {node.id for node in model.nodes}
    
    for support in model.supports:
        assert support.node_id in node_ids
        assert support.type in ["pin", "roller", "fixed"]


def test_detect_structure_scale_independence(sample_image_array):
    """Test that structure detection works with different scale factors."""
    # Should work regardless of scale factor
    model1 = detect_structure(sample_image_array, scale_factor=0.5)
    model2 = detect_structure(sample_image_array, scale_factor=2.0)
    
    # Same topology regardless of scale
    assert len(model1.nodes) == len(model2.nodes)
    assert len(model1.members) == len(model2.members)
    assert len(model1.supports) == len(model2.supports)


def test_detect_structure_truss_properties(sample_image_array):
    """Test that mock truss has expected properties."""
    scale_factor = 1.0
    model = detect_structure(sample_image_array, scale_factor)
    
    # Mock truss should have multiple panels
    # Check for reasonable number of nodes (at least 4 for a simple truss)
    assert len(model.nodes) >= 4
    
    # Should have at least 2 supports
    assert len(model.supports) >= 2
    
    # Members should connect nodes
    assert len(model.members) >= 3
