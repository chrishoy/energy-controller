# Development/debug environment settings
# Production environment settings
from .common import *
import os

# Debug settings
DEBUG = True

# Load settings from environment variables, with fallbacks to development defaults
OCTOPUS_API_KEY = os.getenv("OCTOPUS_API_KEY", "dev-api-key")
OCTOPUS_PRODUCT_CODE = os.getenv("OCTOPUS_PRODUCT_CODE", "dev-product-code").strip('"')
OCTOPUS_TARIFF_CODE = os.getenv("OCTOPUS_TARIFF_CODE", "dev-tariff-code").strip('"')
