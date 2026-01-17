"""Fressnapf API Client."""
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from httpx import AsyncClient

_LOGGER: logging.Logger = logging.getLogger(__name__)


class APIError(Exception):
    """General API error."""


class InvalidDeviceToken(APIError):
    """Invalid device token error."""


class InvalidAuthToken(APIError):
    """Invalid auth token error."""


class InvalidSerialNumber(APIError):
    """Invalid serial number error."""


async def get_fressnapf_response(
    client: AsyncClient, serial_number: int, device_token: str, auth_token: str
) -> dict[str, Any]:
    """Get data from the API."""
    url = f"https://itsmybike.cloud/api/pet_tracker/v2/devices/{serial_number}?devicetoken={device_token}"
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip",
        "authorization": f"Token token={auth_token}",
        "Connection": "keep-alive",
        "Host": "itsmybike.cloud",
        "User-Agent": "okhttp/4.9.2",
        "Content-Type": "application/json",
    }
    response = await client.get(url, headers=headers)
    result = response.json()
    _LOGGER.debug("Result from fressnapf_tracker: %s", result)

    if "error" in result:
        if "Access denied" in result["error"]:
            raise InvalidAuthToken(result["error"])
        if "Invalid devicetoken" in result["error"]:
            raise InvalidDeviceToken(result["error"])
        if "Device not found" in result["error"]:
            raise InvalidSerialNumber(result["error"])
        raise Exception(result["error"])

    """Results from the TRIP-API"""
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    trip_url = f"https://itsmybike.cloud/api/pet_tracker/v2/devices/{serial_number}/trips_from/{one_month_ago}+0:0:0+-60?devicetoken={device_token}"
    response = await client.get(trip_url, headers=headers)
    try:
        trip_result = response.json()
        result["trips"] = trip_result["trips"]
    except Exception:
        result["trips"] = []

    return _transform_result(result)


def _transform_result(result: dict[str, Any]) -> dict[str, Any]:
    """Flatten some entries."""
    if result["tracker_settings"]["features"]["flash_light"]:
        result["led_brightness_value"] = result["led_brightness"]["value"]
        result["led_brightness_status"] = result["led_brightness"]["status"]
        result["led_activatable_overall"] = result["led_activatable"]["overall"]
    if result["tracker_settings"]["features"]["sleep_mode"]:
        result["deep_sleep_value"] = result["deep_sleep"]["value"]
        result["deep_sleep_status"] = result["deep_sleep"]["status"]
    if result["additional_parameters"]:
        try:
            additional_parameters = json.loads(result["additional_parameters"])
        except json.decoder.JSONDecodeError:
            additional_parameters = {}
        result["weight_history"] = additional_parameters["weightList"]
        result["weight_current"] = additional_parameters["weight"].replace(" kg", "")
    return result
