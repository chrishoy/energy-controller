from datetime import datetime
from dataclasses import dataclass, asdict
import json
from typing import List, Optional
import pytz
from json import JSONEncoder


# --- Configuration ---
LOCAL_TZ_NAME = "Europe/London"
LOCAL_TZ = pytz.timezone(LOCAL_TZ_NAME)

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
    data_read_at: Optional[datetime] = None  # When the data was last fetched from Octopus API


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


def zulu_to_local(zulu_time_str: str) -> datetime:
    """Converts a Zulu (UTC) datetime string to a localized datetime object."""
    if zulu_time_str.endswith("Z"):
        zulu_time_str = zulu_time_str[:-1] + "+00:00"

    utc_dt = datetime.fromisoformat(zulu_time_str).replace(tzinfo=pytz.utc)
    local_dt = utc_dt.astimezone(LOCAL_TZ)
    return local_dt
