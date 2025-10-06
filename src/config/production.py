# Production environment settings
from .common import *
import os

# Debug settings
DEBUG = False

# Load sensitive settings from environment variables
OCTOPUS_API_KEY = os.getenv("OCTOPUS_API_KEY")
if not OCTOPUS_API_KEY:
    raise ValueError("OCTOPUS_API_KEY environment variable is required")

# Remove quotes if present in the environment variables
OCTOPUS_PRODUCT_CODE = os.getenv("OCTOPUS_PRODUCT_CODE", "").strip('"')
if not OCTOPUS_PRODUCT_CODE:
    raise ValueError("OCTOPUS_PRODUCT_CODE environment variable is required")

OCTOPUS_TARIFF_CODE = os.getenv("OCTOPUS_TARIFF_CODE", "").strip('"')
if not OCTOPUS_TARIFF_CODE:
    raise ValueError("OCTOPUS_TARIFF_CODE environment variable is required")


# Function kept for backwards compatibility
def load_env_settings():
    """No-op function kept for backwards compatibility."""
    pass  # Environment variables are now loaded when the module is imported
