"""Binary sensor platform for MobileVikings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify

from . import MobileVikingsDataUpdateCoordinator
from .const import DOMAIN, MOBILE_VIKINGS
from .entity import MobileVikingsEntity
from .utils import safe_get

_LOGGER = logging.getLogger(__name__)


@dataclass
class MobileVikingsBinarySensorDescription(SensorEntityDescription):
    """Binary sensor entity description for MobileVikings."""

    available_fn: Callable | None = None
    value_fn: Callable | None = None
    attributes_fn: Callable | None = None
    unique_id_fn: Callable | None = None
    device_name_fn: Callable | None = None
    device_identifier_fn: Callable | None = None
    entity_id_prefix_fn: Callable | None = None
    model_fn: Callable | None = None
    translation_key: str | None = None
    translation_placeholders_fn: Callable | None = None
    subscription_types: tuple[str, ...] | None = None
    bundle_type: str | None = None
    bundle_category: str | None = None
    mobile_platforms: tuple[str, ...] | None = None


SUBSCRIPTION_SENSOR_TYPES: tuple[MobileVikingsBinarySensorDescription, ...] = (
    MobileVikingsBinarySensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="data_usage_alert_all",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_data_usage_alert_all"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: any(
            bundle.get("type") == "data" and not bundle.get("unlimited", False)
            for bundle in data.get("balance", {}).get("bundles", {}).values()
        ),
        value_fn=lambda data, _: all(
            bundle.get("used_percentage", 0) > (bundle.get("period_percentage", 0) + 20)
            for bundle in data.get("balance", {}).get("bundles", {}).values()
            if bundle.get("type") == "data" and not bundle.get("unlimited", False)
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, _: {
            bundle_id: {
                "category": bundle.get("category"),
                "used_percentage": bundle.get("used_percentage"),
                "period_percentage": bundle.get("period_percentage"),
                "alarm_triggered": bundle.get("used_percentage", 0)
                > (bundle.get("period_percentage", 0) + 20),
            }
            for bundle_id, bundle in data.get("balance", {}).get("bundles", {}).items()
            if bundle.get("type") == "data"
        },
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alarm-light",
        mobile_platforms=(MOBILE_VIKINGS,),
    ),
    MobileVikingsBinarySensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid"),
        translation_key="voice_usage_alert",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_voice_usage_alert"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: any(
            bundle.get("type") == "voice"
            for bundle in data.get("balance", {}).get("bundles", {}).values()
        ),
        value_fn=lambda data, _: any(
            (
                safe_get(data, ["balance", "bundles", bundle_id, "used_percentage"], 0)
                > (
                    safe_get(
                        data, ["balance", "bundles", bundle_id, "period_percentage"], 0
                    )
                    + 20
                )
            )
            for bundle_id, bundle in data.get("balance", {}).get("bundles", {}).items()
            if bundle.get("type") == "voice" and not bundle.get("unlimited", False)
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, _: {
            "bundles": {
                bundle_id: {
                    "category": bundle.get("category"),
                    "used_percentage": bundle.get("used_percentage"),
                    "period_percentage": bundle.get("period_percentage"),
                    "unlimited": bundle.get("unlimited", False),
                    "alarm_triggered": (
                        (
                            bundle.get("used_percentage", 0)
                            > (bundle.get("period_percentage", 0) + 20)
                        )
                        if not bundle.get("unlimited", False)
                        else False
                    ),
                }
                for bundle_id, bundle in data.get("balance", {})
                .get("bundles", {})
                .items()
                if bundle.get("type") == "voice"
            }
        },
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alarm-light",
        mobile_platforms=(MOBILE_VIKINGS,),
    ),
    MobileVikingsBinarySensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid"),
        translation_key="sms_usage_alert",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_sms_usage_alert"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: any(
            bundle.get("type") == "sms"
            for bundle in data.get("balance", {}).get("bundles", {}).values()
        ),
        value_fn=lambda data, _: any(
            (
                safe_get(data, ["balance", "bundles", bundle_id, "used_percentage"], 0)
                > (
                    safe_get(
                        data, ["balance", "bundles", bundle_id, "period_percentage"], 0
                    )
                    + 20
                )
            )
            for bundle_id, bundle in data.get("balance", {}).get("bundles", {}).items()
            if bundle.get("type") == "sms" and not bundle.get("unlimited", False)
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, _: {
            "bundles": {
                bundle_id: {
                    "category": bundle.get("category"),
                    "used_percentage": bundle.get("used_percentage"),
                    "period_percentage": bundle.get("period_percentage"),
                    "unlimited": bundle.get("unlimited", False),
                    "alarm_triggered": (
                        (
                            bundle.get("used_percentage", 0)
                            > (bundle.get("period_percentage", 0) + 20)
                        )
                        if not bundle.get("unlimited", False)
                        else False
                    ),
                }
                for bundle_id, bundle in data.get("balance", {})
                .get("bundles", {})
                .items()
                if bundle.get("type") == "sms"
            }
        },
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alarm-light",
        mobile_platforms=(MOBILE_VIKINGS,),
    ),
)

BUNDLE_SENSOR_TYPES: tuple[MobileVikingsBinarySensorDescription, ...] = (
    MobileVikingsBinarySensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="data_usage_alert",
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_data_usage_alert"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: (
            safe_get(
                data, ["balance", "bundles", bundle_id, "used_percentage"], default=0
            )
            > 80
        )
        and not safe_get(
            data, ["balance", "bundles", bundle_id, "unlimited"], default=False
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        ),
        translation_placeholders_fn=lambda data, bundle_id: {
            "category": safe_get(
                data, ["balance", "bundles", bundle_id, "category"], default=""
            )
        },
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alarm-light",
        mobile_platforms=(MOBILE_VIKINGS,),
    ),
    MobileVikingsBinarySensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="rlah_usage_alert",
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_rlah_usage_alert"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "rlah_total"], default=0
        )
        > 0
        and safe_get(data, ["balance", "bundles", bundle_id, "category"], default="")
        != "loyalty",
        value_fn=lambda data, bundle_id: (
            safe_get(
                data,
                ["balance", "bundles", bundle_id, "rlah_used_percentage"],
                default=0,
            )
            > 80
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        ),
        translation_placeholders_fn=lambda data, bundle_id: {
            "category": safe_get(
                data, ["balance", "bundles", bundle_id, "category"], default=""
            )
        },
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:earth",
        mobile_platforms=(MOBILE_VIKINGS,),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MobileVikings binary sensors."""
    _LOGGER.debug("[binary_sensor|async_setup_entry|async_add_entities|start]")
    coordinator: MobileVikingsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    entities: list[MobileVikingsBinarySensor] = []
    mobile_platform = coordinator.client.mobile_platform

    for subscription_id, subscription_data in coordinator.data.get(
        "subscriptions", []
    ).items():
        for sensor_type in SUBSCRIPTION_SENSOR_TYPES:
            if (
                not sensor_type.mobile_platforms
                or mobile_platform not in sensor_type.mobile_platforms
            ):
                _LOGGER.debug(
                    f"Skipping {sensor_type.key}-{sensor_type.translation_key} for mobile platform {mobile_platform}"
                )
                continue
            _LOGGER.debug(
                f"Searching for {sensor_type.key}-{sensor_type.translation_key}"
            )
            if (
                sensor_type.subscription_types is None
                or subscription_data["type"] in sensor_type.subscription_types
            ):
                if sensor_type.key in coordinator.data:
                    entities.append(
                        MobileVikingsBinarySensor(
                            coordinator, sensor_type, entry, subscription_id, None
                        )
                    )

        bundles = subscription_data.get("balance", {}).get("bundles", {})
        for bundle_id, bundle in bundles.items():
            bundle_type = bundle.get("type")
            for sensor_type in BUNDLE_SENSOR_TYPES:
                if mobile_platform not in sensor_type.mobile_platforms:
                    continue
                if (
                    sensor_type.subscription_types is None
                    or subscription_data["type"] in sensor_type.subscription_types
                ):
                    if sensor_type.bundle_type == bundle_type:
                        entities.append(
                            MobileVikingsBinarySensor(
                                coordinator,
                                sensor_type,
                                entry,
                                subscription_id,
                                bundle_id,
                            )
                        )

    async_add_entities(entities)
    return


class MobileVikingsBinarySensor(MobileVikingsEntity, BinarySensorEntity):
    """Representation of an MobileVikings sensor."""

    entity_description: MobileVikingsBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MobileVikingsDataUpdateCoordinator,
        description: EntityDescription,
        entry: ConfigEntry,
        idx: int,
        bundle_id: str | None,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, idx, bundle_id)
        if hasattr(description, "entity_id_prefix_fn") and callable(
            description.entity_id_prefix_fn
        ):
            entity_id_prefix = description.entity_id_prefix_fn(self.item)
        else:
            entity_id_prefix = entry.title
        self.idx = idx
        prefix_part = f"_{slugify(entity_id_prefix)}" if entity_id_prefix else ""
        self.entity_id = f"binary_sensor.{DOMAIN}{prefix_part}_{description.unique_id_fn(self.item, self.bundle_id)}"
        if hasattr(description, "translation_placeholders_fn") and callable(
            description.translation_placeholders_fn
        ):
            self._attr_translation_placeholders = (
                description.translation_placeholders_fn(self.item, self.bundle_id)
            )
        self._value: StateType = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return bool(self.entity_description.value_fn(self.item, self.bundle_id))
        return self._attr_is_on

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}
        attributes = {
            "last_synced": self.last_synced,
        }
        if (
            self.entity_description.attributes_fn
            and self.entity_description.attributes_fn(self.item, self.bundle_id)
            is not None
        ):
            return attributes | self.entity_description.attributes_fn(
                self.item, self.bundle_id
            )
        return attributes
