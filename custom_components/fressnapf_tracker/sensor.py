"""Sensor platform for fressnapf_tracker."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfMass,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .entity import FressnapfTrackerEntity
from . import FressnapfTrackerConfigEntry


SENSOR_ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        name="Battery",
        key="battery",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        name="Weight",
        key="weight_history",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
    ),
)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: FressnapfTrackerConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fressnapf_tracker sensors."""

    coordinator = entry.runtime_data
    sensors: list = []
    for sensor_description in SENSOR_ENTITY_DESCRIPTIONS:
        sensors.append(FressnapfTrackerSensor(coordinator, sensor_description))

    async_add_entities(sensors, True)


class FressnapfTrackerSensor(FressnapfTrackerEntity, SensorEntity):
    """fressnapf_tracker sensor for general information."""

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and bool(self.coordinator.data)

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the resources if it has been received yet."""
        data = self.coordinator.data

        if self.entity_description.key == "weight_history":
            # Aktueller Gewichtswert aus Liste (letzter Eintrag)
            weight_list = data.get("weight_history", [])
            if weight_list:
                try:
                    last_weight = weight_list[-1]["weight"]
                    return float(last_weight.replace(" kg", ""))
                except (ValueError, KeyError):
                    return None

        elif self.entity_description.key in data:
            return float(data[self.entity_description.key])

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return device state attributes."""
        data = self.coordinator.data

        if "weight_history" in data:
            weight_list = data["weight_history"]
            attrs = {}

            for i, entry in enumerate(weight_list, 1):
                timestamp = entry["date"]
                try:
                    date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = str(timestamp)

                attrs[f"history_{i}"] = {
                    "weight": float(entry["weight"].replace(" kg", "")),
                    "date": date_str,
                    "timestamp": timestamp
                }
            return attrs

        return None
