import json
import logging
from dataclasses import dataclass
import os
from typing import List
from tuya_connector import TuyaOpenAPI, TUYA_LOGGER
from tuya_config import API_ENDPOINT, API_DEVICES, API_THING


@dataclass
class DeviceTemperature:
    device_id: str
    temperature: float


def connect():
    """Connect to Tuya Cloud Services and return the OpenAPI object"""

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Init OpenAPI and connect
    print("\n🔍 Connecting to Tuya Cloud Services:")
    access_id = os.getenv("TUYA_ACCESS_ID")
    access_key = os.getenv("TUYA_ACCESS_KEY")
    openapi = TuyaOpenAPI(API_ENDPOINT, access_id, access_key)
    response = openapi.connect()
    print(json.dumps(response, indent=2))
    return openapi


# === Query device properties ===
def query_device_properties(openapi, device_id: str):
    """
    Query the current properties of a device
    """

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Verify connected via OpenAPI
    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    # Get the status of a single device
    response = openapi.get(f"{API_THING}{device_id}/shadow/properties")
    return response["result"]["properties"]


def try_set_thermostat_temperature(openapi, device_temp: DeviceTemperature):
    """
    Attempts to set thermostat to 'hold' mode if not OFF and in 'smart' mode\n
    Set temperature in 0.1 degree increments\n
    Only works if thermostat is ON and either in 'hold' or 'smart' mode
    """

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Verify connected via OpenAPI
    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    # Ensure thermostat is ON and in HOLD mode
    if try_set_thermostat_hold_mode(openapi, device_temp.device_id):
        print(
            f"🔍 Setting temperature for thermostat "
            "device id '{device_temp.device_id}' "
            f"to {device_temp.temperature}°C"
        )

        property_value = round(device_temp.temperature * 10)
        data = {"properties": f'{{"SetTemp": {property_value}}}'}

        response = openapi.post(
            f"{API_THING}{device_temp.device_id}/shadow/properties/issue", data
        )

        return response["success"]

    return False


def try_set_thermostat_hold_mode(openapi, device_id: str) -> bool:
    """
    Set thermostat to 'hold' mode\n
    Only works if thermostat is ON and in smart mode (i.e. not in holiday mode or OFF)
    """

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Verify connected via OpenAPI
    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    current_props = query_device_properties(openapi, device_id)

    if is_on(current_props):
        if is_hold_mode(current_props):
            print(f"Thermostat device id '{device_id}' already in HOLD mode")
            return True

        if is_smart_mode(current_props):
            print(f"\n🔍 Setting HOLD mode for thermostat device id '{device_id}'")
            post_data = {"properties": '{"ControlMode":"hold"}'}
            response = openapi.post(
                f"{API_THING}{device_id}/shadow/properties/issue", post_data
            )
            return response["success"]

    return False


def is_on(properties) -> bool:
    value = next((p["value"] for p in properties if p["code"] == "power1"), None)
    if value is False:
        print("Thermostat is OFF - cannot set temperature")
        return False
    return True


def is_smart_mode(properties) -> bool:
    value = next((p["value"] for p in properties if p["code"] == "ControlMode"), None)
    if value == "smart":
        return True
    return False


def is_hold_mode(properties) -> bool:
    value = next((p["value"] for p in properties if p["code"] == "ControlMode"), None)
    if value == "hold":
        return True
    return False


# === Set temperature ===
def try_set_thermostat_temperatures(
    openapi, device_temps: List[DeviceTemperature]
) -> bool:
    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return False

    all_succeeded = True
    for device_temp in device_temps:
        print(f"\n🔍 Setting temperature for device '{device_temp.device_id}'")
        all_succeeded = all_succeeded and try_set_thermostat_temperature(
            openapi, device_temp
        )

    # Report overall success
    if all_succeeded:
        print("All temperatures set for thermostats")
        return True

    print("Failed to set one or more thermostat temperatures")
    return False


def try_turn_thermostat_on(openapi, device_id: str):
    """
    Attempts to set thermostat ON
    """

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Verify connected via OpenAPI
    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    current_props = query_device_properties(openapi, device_id)

    if is_on(current_props):
        print(f"Thermostat device id '{device_id}' already in ON")
        return True

    post_data = {"properties": '{"power1": True}'}

    response = openapi.post(
        f"{API_THING}{device_id}/shadow/properties/issue", post_data
    )

    return response["success"]


def try_turn_thermostat_off(openapi, device_id: str):
    """
    Attempts to set thermostat OFF
    """

    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    # Verify connected via OpenAPI
    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    current_props = query_device_properties(openapi, device_id)

    if not is_on(current_props):
        print(f"Thermostat device id '{device_id}' already in OFF")
        return True

    post_data = {"properties": '{"power1": False}'}

    response = openapi.post(
        f"{API_THING}{device_id}/shadow/properties/issue", post_data
    )

    return response["success"]


# === Turn device OFF ===
def turn_off(openapi, device_id: str):
    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    current_props = query_device_properties(openapi, device_id)

    if not is_on(current_props):
        print(f"Thermostat device id '{device_id}' already in OFF")
        return True

    # Send commands
    commands = {"commands": [{"code": "switch", "value": False}]}
    response = openapi.post(f"{API_DEVICES}{device_id}/commands", commands)

    success = response["success"]
    if success:
        print(f"Thermostat device id '{device_id}' turned OFF")
        return True
    else:
        print(f"Failed to turn OFF device id '{device_id}'")
        return False


# === Turn device ON ===
def turn_on(openapi, device_id: str) -> bool:
    # Enable debug log
    TUYA_LOGGER.setLevel(logging.DEBUG)

    if openapi is None:
        print("\n🔍 Not connected to Tuya Cloud Services")
        return None

    current_props = query_device_properties(openapi, device_id)

    if is_on(current_props):
        print(f"Thermostat device id '{device_id}' already in ON")
        return True

    commands = {"commands": [{"code": "switch", "value": True}]}
    response = openapi.post(f"{API_DEVICES}{device_id}/commands", commands)

    success = response["success"]
    if success:
        print(f"Thermostat device id '{device_id}' turned ON")
        return True
    else:
        print(f"Failed to turn ON device id '{device_id}'")
        return False
