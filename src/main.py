from heating_controller import (
    DeviceTemperature,
    connect,
    try_set_thermostat_temperatures,
    try_turn_thermostat_off,
)
from octopus_api import get_octopus_rates
from optimiser import optimize_heating_schedule
from print_utils import print_optimised_heating_schedule

LIVING_ROOM_DEVICE_ID = "bf945c82fa2de02aea8ifa"
KITCHEN_DEVICE_ID = "bfaa6f1c0d720a9820cgaz"
STORE_ROOM_DEVICE_ID = "bf66bbc34a971689523ly2"
UTILITY_ROOM_DEVICE_ID = "bfb455b47dec93c352duhk"

if __name__ == "__main__":

    # print("\n🔍 Current thermostat status:")
    openapi = connect()

    # set_device_temperatures(openapi, device_temperatures_high)
    # device_temp = DeviceTemperature(device_id=LIVING_ROOM_DEVICE_ID, temperature=15)
    # result = try_set_thermostat_temperature(openapi, device_temp)

    # 1. Get current and future energy rates from Octopus Energy API
    rates = get_octopus_rates()
    latest_rates = rates.latest
    optimised_heating_schedule = optimize_heating_schedule(latest_rates)
    print_optimised_heating_schedule(optimised_heating_schedule)

    off_result = try_turn_thermostat_off(openapi, LIVING_ROOM_DEVICE_ID)

    device_temperatures_low = [
        DeviceTemperature(device_id=LIVING_ROOM_DEVICE_ID, temperature=5),
        DeviceTemperature(device_id=KITCHEN_DEVICE_ID, temperature=5),
        DeviceTemperature(device_id=UTILITY_ROOM_DEVICE_ID, temperature=5),
        DeviceTemperature(device_id=STORE_ROOM_DEVICE_ID, temperature=5),
    ]

    device_temperatures_high = [
        DeviceTemperature(device_id=LIVING_ROOM_DEVICE_ID, temperature=22),
        DeviceTemperature(device_id=KITCHEN_DEVICE_ID, temperature=22),
        DeviceTemperature(device_id=UTILITY_ROOM_DEVICE_ID, temperature=22),
        DeviceTemperature(device_id=STORE_ROOM_DEVICE_ID, temperature=22),
    ]

    try_set_thermostat_temperatures(openapi, device_temperatures_low)

    # print("Starting Energy Controller...")
    # start_scheduler()
    # print("Scheduler started.")
