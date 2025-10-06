"""Configuration management module for the energy controller."""

import os
import importlib
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


def get_config() -> Any:
    """
    Get the configuration based on the environment.

    Returns:
        module: The configuration module for the current environment
    """
    env = os.getenv("ENERGY_CONTROLLER_ENV", "development").lower()
    if env not in ("development", "production"):
        raise ValueError(
            f"Invalid environment: {env}. Must be 'development' or 'production'"
        )

    config = importlib.import_module(f".{env}", package="src.config")

    # If in production, load environment variables
    if env == "production":
        config.load_env_settings()

    return config
