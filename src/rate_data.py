"""Data structures for rate information."""

from datetime import datetime
from dataclasses import dataclass, asdict
import json
from typing import List, Optional
from json import JSONEncoder
from .utils.date_utils import LOCAL_TZ

# --- Data Classes ---


@dataclass
class Rate:
    """Represents a single half-hourly unit rate in pence per kWh."""

    value_exc_vat: float
    value_inc_vat: float
    # We will use ISO 8601 strings for serialization
    valid_from: datetime  # Localized datetime
    valid_to: datetime  # Localized datetime


@dataclass
class RateData:
    """The top-level structure for the returned rate data."""

    latest: List[Rate]
    current: Optional[Rate]
    as_at: datetime  # Localized datetime
    data_read_at: Optional[datetime] = (
        None  # When the data was last fetched from Octopus API
    )


# --- Custom JSON Encoder for Dataclasses and Datetime ---


class RateDataEncoder(JSONEncoder):
    """
    Custom JSONEncoder to serialize RateData, Rate, and datetime objects.
    """

    def default(self, obj):
        # Handle dataclasses (RateData and Rate)
        if isinstance(obj, (RateData, Rate)):
            # Convert dataclass instance to a dictionary
            return asdict(obj)

        # Handle datetime objects
        if isinstance(obj, datetime):
            # Convert datetime objects to ISO 8601 strings (includes timezone info)
            return obj.isoformat()

        # Let the base class handle other types
        return super().default(obj)


# --- Utility Functions ---
def rate_data_to_json(price_data: RateData) -> str:
    """
    Converts the RateData object into a JSON string using the custom encoder.
    """
    # Use the custom encoder and set ensure_ascii=False for proper characters
    return json.dumps(price_data, indent=4, cls=RateDataEncoder, ensure_ascii=False)
