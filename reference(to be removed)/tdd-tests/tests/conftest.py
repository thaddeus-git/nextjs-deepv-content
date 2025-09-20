#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for DeepV StackOverflow Workflow tests
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Get project root directory path"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session") 
def sample_stackoverflow_data():
    """Load sample StackOverflow data for all tests"""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_stackoverflow.json"
    with open(fixtures_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def config_manager():
    """Mock configuration manager for testing"""
    pytest.skip("ConfigManager tests not implemented yet")


@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter API client for testing"""
    pytest.skip("OpenRouter client mocking not implemented yet")


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark all tests in test_dynamic_tokens.py as unit tests
        if "test_dynamic_tokens" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
            
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# Custom pytest options
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-slow", 
        action="store_true", 
        default=False, 
        help="run slow tests"
    )


def pytest_runtest_setup(item):
    """Setup for individual test runs"""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")