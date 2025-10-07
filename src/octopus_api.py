import requests
import json
import logging
from datetime import datetime, time, timedelta
from typing import List, Optional
import pytz
from .config import get_config
from .rate_data import LOCAL_TZ, Rate, RateData, zulu_to_local, rate_data_to_json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_current_rate(latest_prices: List[Rate]) -> tuple[datetime, Optional[Rate]]:
    """
    Determines the current rate from a list of rates based on the current time.
    
    Args:
        latest_prices: List of Rate objects sorted by valid_from time
        
    Returns:
        Tuple of (current datetime with timezone, current rate or None if not found)
    """
    as_at_dt = datetime.now(LOCAL_TZ)
    current_rate = None
    for price in latest_prices:
        if price.valid_from <= as_at_dt < price.valid_to:
            current_rate = price
            break
    return as_at_dt, current_rate


def get_cached_rates() -> Optional[RateData]:
    """
    Attempts to load cached rate data from latest_prices.json.
    Returns None if the cache doesn't exist or is invalid.
    """
    try:
        with open("latest_prices.json", "r") as f:
            cached_data = json.loads(f.read())
            
        # Check if cache is still valid (less than 30 minutes old)
        cached_time = datetime.fromisoformat(cached_data["as_at"])
        age = datetime.now(LOCAL_TZ) - cached_time
        if age < timedelta(minutes=30):
            logger.info(f"Using cached data from {age.total_seconds() / 60:.1f} minutes ago")
            # Reconstruct Rate objects from cached JSON
            latest_prices = [
                Rate(
                    value_exc_vat=rate["value_exc_vat"],
                    value_inc_vat=rate["value_inc_vat"],
                    valid_from=datetime.fromisoformat(rate["valid_from"]),
                    valid_to=datetime.fromisoformat(rate["valid_to"])
                )
                for rate in cached_data["latest"]
            ]
            
            # Find current rate based on current time
            as_at_dt, current_rate = get_current_rate(latest_prices)
            
            data_read_at = (
                datetime.fromisoformat(cached_data["data_read_at"])
                if "data_read_at" in cached_data
                else None
            )
            
            return RateData(
                latest=latest_prices,
                current=current_rate,
                as_at=as_at_dt,
                data_read_at=data_read_at
            )
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        return None


def get_octopus_rates() -> RateData:
    """
    Fetches rates, saves raw data, and returns a RateData dataclass
    with current and historical local-time prices.
    Uses cached data if available and less than 30 minutes old.
    """
    # Try to get cached data first
    cached_data = get_cached_rates()
    if cached_data:
        return cached_data

    # If no valid cache, fetch fresh data
    logger.info("Cache miss or expired, fetching fresh data from Octopus API")
    # 1. Setup API Details and Time Parameters
    config = get_config()
    api_key = config.OCTOPUS_API_KEY
    product_code = config.OCTOPUS_PRODUCT_CODE
    tariff_code = config.OCTOPUS_TARIFF_CODE
    octopus_base_url = config.OCTOPUS_BASE_URL

    # Calculate 'period_from' and 'period_to' (Start of today to day after tomorrow)
    now_local = datetime.now(LOCAL_TZ)
    start_of_today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    # CORRECTED LOGIC for end_period_local:
    day_after_tomorrow_date = now_local.date() + timedelta(days=2)
    start_of_day_after_tomorrow_naive = datetime.combine(
        day_after_tomorrow_date, time.min
    )
    end_period_local = LOCAL_TZ.localize(start_of_day_after_tomorrow_naive)

    # Convert to ISO 8601 Zulu format required by the API
    period_from = (
        start_of_today_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")
    )
    period_to = end_period_local.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")

    standard_elec_rates_url = (
        f"{octopus_base_url}/{product_code}/electricity-tariffs/"
        f"{tariff_code}/standard-unit-rates/"
    )

    params = {"period_from": period_from, "period_to": period_to, "page_size": 100}

    # 2. Make API Request and Save Raw Data
    response = requests.get(standard_elec_rates_url, auth=(api_key, ""), params=params)
    response.raise_for_status()
    data = response.json()

    with open("current_prices_raw.json", "w") as f:
        json.dump(data, f, indent=4)

    # 3. Process Data
    latest_prices: List[Rate] = []

    for result in data["results"]:
        valid_from_local = zulu_to_local(result["valid_from"])
        valid_to_local = zulu_to_local(result["valid_to"])

        price_item = Rate(
            value_exc_vat=result["value_exc_vat"],
            value_inc_vat=result["value_inc_vat"],
            valid_from=valid_from_local,
            valid_to=valid_to_local,
        )
        latest_prices.append(price_item)

    latest_prices.sort(key=lambda r: r.valid_from)

    # 4. Determine 'current' Price
    as_at_dt, current_price = get_current_rate(latest_prices)

    # 5. Return the final RateData object
    price_data = RateData(
        latest=latest_prices,
        current=current_price,
        as_at=as_at_dt,
        data_read_at=as_at_dt
    )
    price_data_json = rate_data_to_json(price_data)
    with open("latest_prices.json", "w") as f:
        f.write(price_data_json)

    return price_data
