"""MobileVikings sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import MobileVikingsDataUpdateCoordinator
from .const import DOMAIN
from .entity import MobileVikingsEntity
from .models import MobileVikingsItem
from .utils import log_debug


@dataclass
class MobileVikingsSensorDescription(SensorEntityDescription):
    """Class to describe a MobileVikings sensor."""

    value_fn: Callable[[Any], StateType] | None = None


SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    MobileVikingsSensorDescription(key="profile", icon="mdi:face-man"),
    MobileVikingsSensorDescription(key="subscription", icon="mdi:sim"),
    MobileVikingsSensorDescription(
        key="euro",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="euro_blocked",
        icon="mdi:currency-eur-off",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="euro_pending",
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="usage_percentage_mobile",
        value_fn=lambda state: round(state, 1),
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:signal-4g",
    ),
    MobileVikingsSensorDescription(
        key="remaining_days",
        icon="mdi:calendar-end-outline",
    ),
    MobileVikingsSensorDescription(
        key="invoices",
        icon="mdi:receipt-text-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MobileVikingsSensorDescription(
        key="date",
        icon="mdi:calendar-star",
        device_class=SensorDeviceClass.DATE,
    ),
    MobileVikingsSensorDescription(key="address", icon="mdi:home"),
    MobileVikingsSensorDescription(key="voice", icon="mdi:phone"),
    MobileVikingsSensorDescription(key="sms", icon="mdi:message-processing"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MobileVikings sensors."""
    log_debug("[sensor|async_setup_entry|async_add_entities|start]")
    coordinator: MobileVikingsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[MobileVikingsSensor] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SENSOR_DESCRIPTIONS
    }

    # log_debug(f"[sensor|async_setup_entry|async_add_entities|SUPPORTED_KEYS] {SUPPORTED_KEYS}")

    if coordinator.data is not None:
        for item in coordinator.data:
            item = coordinator.data[item]
            if description := SUPPORTED_KEYS.get(item.type):
                if item.native_unit_of_measurement is not None:
                    native_unit_of_measurement = item.native_unit_of_measurement
                else:
                    native_unit_of_measurement = description.native_unit_of_measurement
                sensor_description = MobileVikingsSensorDescription(
                    key=str(item.key),
                    name=item.name,
                    value_fn=description.value_fn,
                    native_unit_of_measurement=native_unit_of_measurement,
                    icon=description.icon,
                )

                log_debug(f"[sensor|async_setup_entry|adding] {item.name}")
                entities.append(
                    MobileVikingsSensor(
                        coordinator=coordinator,
                        description=sensor_description,
                        item=item,
                    )
                )
            else:
                log_debug(
                    f"[sensor|async_setup_entry|no support type found] {item.name}, type: {item.type}, keys: {SUPPORTED_KEYS.get(item.type)}",
                    True,
                )

        async_add_entities(entities)


class MobileVikingsSensor(MobileVikingsEntity, SensorEntity):
    """Representation of a MobileVikings sensor."""

    entity_description: MobileVikingsSensorDescription

    def __init__(
        self,
        coordinator: MobileVikingsDataUpdateCoordinator,
        description: EntityDescription,
        item: MobileVikingsItem,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, item)
        self.entity_id = f"sensor.{DOMAIN}_{self.item.key}"

    @property
    def native_value(self) -> str:
        """Return the status of the sensor."""
        state = self.item.state

        if self.entity_description.value_fn:
            return self.entity_description.value_fn(state)

        return state

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}
        attributes = {
            "last_synced": self.last_synced,
        }
        if len(self.item.extra_attributes) > 0:
            for attr in self.item.extra_attributes:
                attributes[attr] = self.item.extra_attributes[attr]
        return attributes
