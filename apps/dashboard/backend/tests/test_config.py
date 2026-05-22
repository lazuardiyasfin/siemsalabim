"""Tests for Dashboard Backend config."""

import os
from unittest.mock import patch


from dashboard_backend.config import DashboardConfig


def test_config_defaults():
    """Test DashboardConfig with default values."""
    with patch.dict(os.environ, {}, clear=True):
        config = DashboardConfig()

        assert config.engine_url == "ws://localhost:8000/ws/dashboard"
        assert config.host == "0.0.0.0"
        assert config.port == 8001


def test_config_from_env():
    """Test DashboardConfig loads from environment variables."""
    env_vars = {
        "DASHBOARD_ENGINE_URL": "ws://engine:8000/ws/dashboard",
        "DASHBOARD_HOST": "127.0.0.1",
        "DASHBOARD_PORT": "9001",
    }

    with patch.dict(os.environ, env_vars):
        config = DashboardConfig()

        assert config.engine_url == "ws://engine:8000/ws/dashboard"
        assert config.host == "127.0.0.1"
        assert config.port == 9001


def test_config_partial_env():
    """Test DashboardConfig with partial environment variables."""
    env_vars = {
        "DASHBOARD_ENGINE_URL": "ws://custom:8000/ws/dashboard",
    }

    with patch.dict(os.environ, env_vars):
        config = DashboardConfig()

        assert config.engine_url == "ws://custom:8000/ws/dashboard"
        assert config.host == "0.0.0.0"  # Default
        assert config.port == 8001  # Default


def test_config_prefix():
    """Test that config uses correct env prefix."""
    # These should be ignored because they don't have DASHBOARD_ prefix
    env_vars = {
        "ENGINE_URL": "ws://wrong:8000/ws/dashboard",
        "HOST": "127.0.0.1",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = DashboardConfig()

        assert config.engine_url == "ws://localhost:8000/ws/dashboard"  # Default
        assert config.host == "0.0.0.0"  # Default


def test_config_port_type_conversion():
    """Test that port is converted to integer."""
    env_vars = {
        "DASHBOARD_PORT": "5000",
    }

    with patch.dict(os.environ, env_vars):
        config = DashboardConfig()

        assert isinstance(config.port, int)
        assert config.port == 5000


def test_config_model_config():
    """Test DashboardConfig model configuration."""
    config = DashboardConfig()

    # Check that the model has env_prefix set correctly
    assert config.model_config.get("env_prefix") == "DASHBOARD_"
