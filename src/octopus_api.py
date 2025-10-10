import requests
import json
import logging
from datetime import datetime, time, timedelta
from typing import List, Optional
from pathlib import Path

from .config import get_config
from .rate_data import Rate, RateData
from .utils.date_utils import (
    LOCAL_TZ,
    zulu_to_local,
    local_to_zulu_str,
    datetime_to_json_str,
    json_str_to_datetime,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_FILE = Path("latest_prices.json")
CACHE_EXPIRY_HOURS = 2
DATA_WINDOW_HOURS = 48


# ----------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------


def get_current_rate(latest_prices: List[Rate]) -> tuple[datetime, Optional[Rate]]:
    """Determines the current rate from a list of rates."""
    as_at_dt = datetime.now(LOCAL_TZ)
    for price in latest_prices:
        if price.valid_from <= as_at_dt < price.valid_to:
            return as_at_dt, price
    return as_at_dt, None


def merge_price_data(existing_prices: List[Rate], new_prices: List[Rate]) -> List[Rate]:
    """
    Merges two lists of rates, removing duplicates. New prices take precedence.
    """
    combined_prices = existing_prices + new_prices

    seen_times = set()
    unique_prices = []
    # Iterate backwards to give precedence to new_prices items
    for price in reversed(combined_prices):
        if price.valid_from not in seen_times:
            unique_prices.append(price)
            seen_times.add(price.valid_from)

    unique_prices.reverse()  # Restore chronological order
    logger.info(
        f"Merged price data: {len(existing_prices)} existing + "
        f"{len(new_prices)} new = {len(unique_prices)} unique rates."
    )
    return unique_prices


def _fetch_new_rates_from_api() -> List[Rate]:
    """Fetches the latest electricity rates from the Octopus Energy API."""
    logger.info("Fetching fresh data from Octopus API.")
    config = get_config()

    # Define the time window for the API request (today and tomorrow)
    now_local = datetime.now(LOCAL_TZ)
    start_period = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_period = start_period + timedelta(days=2)

    api_url = (
        f"{config.OCTOPUS_BASE_URL}/{config.OCTOPUS_PRODUCT_CODE}/electricity-tariffs/"
        f"{config.OCTOPUS_TARIFF_CODE}/standard-unit-rates/"
    )
    params = {
        "period_from": local_to_zulu_str(start_period),
        "period_to": local_to_zulu_str(end_period),
        "page_size": 150,  # Sufficient for 2 days of 30-min slots
    }

    try:
        response = requests.get(
            api_url, auth=(config.OCTOPUS_API_KEY, ""), params=params
        )
        response.raise_for_status()
        data = response.json()

        # Process the API response into Rate objects
        new_rates = [
            Rate(
                value_exc_vat=r["value_exc_vat"],
                value_inc_vat=r["value_inc_vat"],
                valid_from=zulu_to_local(r["valid_from"]),
                valid_to=zulu_to_local(r["valid_to"]),
            )
            for r in data.get("results", [])
        ]
        new_rates.sort(key=lambda r: r.valid_from)
        return new_rates
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.error(f"Failed to fetch or parse data from Octopus API: {e}")
        return []


def _load_rates_from_cache() -> Optional[List[Rate]]:
    """Loads rates from the cache if the file exists."""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r") as f:
            cached_data = json.load(f)
        return [
            Rate(
                value_exc_vat=rate["value_exc_vat"],
                value_inc_vat=rate["value_inc_vat"],
                valid_from=json_str_to_datetime(rate["valid_from"]),
                valid_to=json_str_to_datetime(rate["valid_to"]),
            )
            for rate in cached_data
        ]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error reading cache file {CACHE_FILE}: {e}")
        return None


def _save_rates_to_cache(rates: List[Rate]) -> None:
    """Saves a list of rates to the cache file."""
    logger.info(f"Saving {len(rates)} rates to cache file: {CACHE_FILE}")
    serializable_rates = [
        {
            "value_exc_vat": rate.value_exc_vat,
            "value_inc_vat": rate.value_inc_vat,
            "valid_from": datetime_to_json_str(rate.valid_from),
            "valid_to": datetime_to_json_str(rate.valid_to),
        }
        for rate in rates
    ]
    with open(CACHE_FILE, "w") as f:
        json.dump(serializable_rates, f, indent=4)


def _filter_rates_to_window(rates: List[Rate], hours: int) -> List[Rate]:
    """
    Filters rates to include only those from the start of yesterday.

    This ensures the data window always begins at 00:00 of the previous day
    in the local timezone, up to the latest available rate. For example, if run
    on October 10th, it will include all rate slots from October 9th at 00:00:00
    onwards.

    Args:
        rates: The list of Rate objects to filter.
        hours: This parameter is ignored to conform to the new logic but is
               kept for method signature consistency.

    Returns:
        A new list of Rate objects filtered to the specified time window.
    """
    # 1. Determine the start of yesterday in the local timezone.
    now_local = datetime.now(LOCAL_TZ)
    yesterday_date = now_local.date() - timedelta(days=1)

    # Create a datetime object for yesterday at midnight.
    start_of_yesterday_naive = datetime.combine(yesterday_date, time.min)

    # Make the datetime object timezone-aware.
    cutoff = LOCAL_TZ.localize(start_of_yesterday_naive)

    # 2. Filter the rates. We keep any rate slot that *ends* after midnight yesterday.
    # This correctly includes all slots starting from 00:00 yesterday.
    filtered_rates = [rate for rate in rates if rate.valid_to > cutoff]

    logger.info(
        f"Filtered rates to include data since {cutoff.strftime('%Y-%m-%d %H:%M')}. "
        f"Kept {len(filtered_rates)} out of {len(rates)} rates."
    )

    return filtered_rates


# ----------------------------------------------------------------------------
# Main Orchestration Method
# ----------------------------------------------------------------------------


def get_octopus_rates() -> RateData:
    """
    Fetches rates, using a cache-then-API strategy,
    and returns data for the last 48 hours.

    This function follows these steps:
    1.  Tries to load fresh data from a local cache.
    2.  If the cache is valid, returns the data immediately.
    3.  If the cache is stale or missing, it fetches new data from the Octopus API.
    4.  It merges the new data with any existing (but stale) cached data.
    5.  It filters the merged list to only include the most recent 48 hours of data.
    6.  The result is saved to the cache and returned.
    """
    # 1. Check for valid, recent cache
    cached_rates = _load_rates_from_cache()
    if cached_rates:
        cache_age = datetime.now(LOCAL_TZ) - datetime.fromtimestamp(
            CACHE_FILE.stat().st_mtime, LOCAL_TZ
        )
        if cache_age < timedelta(hours=CACHE_EXPIRY_HOURS):
            logger.info(
                f"Using fresh cache data ({cache_age.total_seconds() / 60:.1f} mins old)."
            )
            final_rates = _filter_rates_to_window(cached_rates, hours=DATA_WINDOW_HOURS)
            as_at_dt, current_rate = get_current_rate(final_rates)
            return RateData(
                latest=final_rates,
                current=current_rate,
                as_at=as_at_dt,
                data_read_at=datetime.fromtimestamp(
                    CACHE_FILE.stat().st_mtime, LOCAL_TZ
                ),
            )

    # 2. Fetch new data from API if cache is stale or missing
    new_rates = _fetch_new_rates_from_api()
    if not new_rates:
        logger.error("No new rates fetched. Returning empty data.")
        return RateData(
            latest=[],
            current=None,
            as_at=datetime.now(LOCAL_TZ),
            data_read_at=datetime.now(LOCAL_TZ),
        )

    # 3. Merge new rates with any existing (stale) cache
    existing_rates = cached_rates or []
    merged_rates = merge_price_data(existing_rates, new_rates)

    # 4. Filter merged data to the desired 48-hour window
    final_rates = _filter_rates_to_window(merged_rates, hours=DATA_WINDOW_HOURS)

    # 5. Save the final, clean data to cache
    _save_rates_to_cache(final_rates)

    # 6. Prepare and return the RateData object
    data_read_at = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime, LOCAL_TZ)
    as_at_dt, current_rate = get_current_rate(final_rates)

    return RateData(
        latest=final_rates,
        current=current_rate,
        as_at=as_at_dt,
        data_read_at=data_read_at,
    )
