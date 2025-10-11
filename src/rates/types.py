"""Data structures for rate information."""

from datetime import datetime
from dataclasses import dataclass, asdict
import json
from typing import Any, List, Optional
from json import JSONEncoder

from src.utils.date_utils import datetime_to_json_str

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


def rate_data_to_object(rate_data: RateData) -> dict[str, Any]:
    current_rate = rate_data.current
    data = {
        "as_at": datetime_to_json_str(rate_data.as_at),
        "data_read_at": datetime_to_json_str(rate_data.data_read_at),
        "current": {
            "value_exc_vat": (current_rate.value_exc_vat if current_rate else None),
            "value_inc_vat": (current_rate.value_inc_vat if current_rate else None),
            "valid_from": (
                datetime_to_json_str(current_rate.valid_from) if current_rate else None
            ),
            "valid_to": (
                datetime_to_json_str(current_rate.valid_to) if current_rate else None
            ),
        },
        "latest": [
            {
                "value_exc_vat": rate.value_exc_vat,
                "value_inc_vat": rate.value_inc_vat,
                "valid_from": datetime_to_json_str(rate.valid_from),
                "valid_to": datetime_to_json_str(rate.valid_to),
            }
            for rate in rate_data.latest
        ],
    }
    return data
