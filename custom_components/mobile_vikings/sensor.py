"""MobileVikings sensor platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Callable, Optional, Tuple

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO, PERCENTAGE, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify

from . import MobileVikingsDataUpdateCoordinator
from .const import DOMAIN
from .entity import MobileVikingsEntity
from .utils import safe_get, to_title_case_with_spaces

_LOGGER = logging.getLogger(__name__)


@dataclass
class MobileVikingsSensorDescription(SensorEntityDescription):
    """Sensor entity description for MobileVikings."""

    available_fn: Callable | None = None
    value_fn: Callable | None = None
    attributes_fn: Callable | None = None
    unique_id_fn: Callable | None = None
    device_name_fn: Callable | None = None
    device_identifier_fn: Callable | None = None
    entity_id_prefix_fn: Callable | None = None
    model_fn: Callable | None = None
    translation_key: str | None = None
    subscription_types: Optional[Tuple[str, ...]] = (
        None  # Optional list of subscription types
    )


SENSOR_TYPES: tuple[MobileVikingsSensorDescription, ...] = (
    MobileVikingsSensorDescription(
        key="customer_info",
        translation_key="customer_info",
        unique_id_fn=lambda data: "customer_info",
        icon="mdi:face-man",
        available_fn=lambda data: data.get("first_name") is not None,
        value_fn=lambda data: data.get("first_name"),
        device_name_fn=lambda data: "Customer",
        device_identifier_fn=lambda data: "Customer",
        model_fn=lambda data: "Customer Info",
        attributes_fn=lambda data: data,
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_available",
        unique_id_fn=lambda data: "loyalty_points_available",
        icon="mdi:currency-eur",
        available_fn=lambda data: data.get("available") is not None,
        value_fn=lambda data: data.get("available"),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_blocked",
        unique_id_fn=lambda data: "loyalty_points_blocked",
        icon="mdi:currency-eur-off",
        available_fn=lambda data: data.get("blocked") is not None,
        value_fn=lambda data: data.get("blocked"),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_pending",
        unique_id_fn=lambda data: "loyalty_points_pending",
        icon="mdi:timer-sand",
        available_fn=lambda data: data.get("pending") is not None,
        value_fn=lambda data: data.get("pending"),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="paid_invoices",
        translation_key="paid_invoices",
        unique_id_fn=lambda data: "paid_invoices",
        icon="mdi:receipt-text-check",
        available_fn=lambda data: data.get("results") is not None,
        value_fn=lambda data: data.get("total_items"),
        device_name_fn=lambda data: "Invoices",
        device_identifier_fn=lambda data: "Invoices",
        model_fn=lambda data: "Invoices",
        attributes_fn=lambda data: {
            "invoices": safe_get(data, ["results"], default=[])
        },
    ),
    MobileVikingsSensorDescription(
        key="unpaid_invoices",
        translation_key="unpaid_invoices",
        unique_id_fn=lambda data: "unpaid_invoices",
        icon="mdi:currency-eur",
        available_fn=lambda data: data.get("results") is not None,
        value_fn=lambda data: sum(
            item.get("amount_due", 0) for item in data.get("results", [])
        ),
        device_name_fn=lambda data: "Invoices",
        device_identifier_fn=lambda data: "Invoices",
        model_fn=lambda data: "Invoices",
        attributes_fn=lambda data: {
            "invoices": safe_get(data, ["results"], default=[])
        },
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
    ),
    MobileVikingsSensorDescription(
        key="unpaid_invoices",
        translation_key="next_invoice_expiration",
        unique_id_fn=lambda data: "next_invoice_expiration",
        icon="mdi:calendar-star",
        available_fn=lambda data: data.get("results") is not None,
        value_fn=lambda data: min(
            (
                datetime.fromisoformat(item["expiration_date"].replace("Z", "+00:00"))
                for item in data.get("results", [])
                if "expiration_date" in item
            ),
            default=None,
        ),
        device_name_fn=lambda data: "Invoices",
        device_identifier_fn=lambda data: "Invoices",
        model_fn=lambda data: "Invoices",
        attributes_fn=lambda data: {
            "days_until_next_expiration_date": (
                (
                    min(
                        (
                            datetime.fromisoformat(
                                item["expiration_date"].replace("Z", "+00:00")
                            )
                            for item in data.get("results", [])
                            if "expiration_date" in item
                        ),
                        default=None,
                    )
                    - datetime.now(timezone.utc)
                ).days
                if data.get("results")
                else None
            ),
            "results": safe_get(data, ["results"], default={}),
        },
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)

SUBSCRIPTION_SENSOR_TYPES: tuple[MobileVikingsSensorDescription, ...] = (
    # Data balance
    MobileVikingsSensorDescription(
        key="subscriptions",
        translation_key="data_balance",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_data_balance"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("data", {})
        .get("used_percentage")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data", "used_percentage"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data"], default={}
        ),
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:signal-4g",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="data_remaining",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_data_remaining"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("data", {})
        .get("remaining_gb")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data", "remaining_gb"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data"], default={}
        ),
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        icon="mdi:signal-4g",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="remaining_days",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_remaining_days"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("data", {})
        .get("remaining_days")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data", "remaining_days"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:calendar-end-outline",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="period_percentage",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_period_pct"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("data", {})
        .get("period_percentage")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "data", "period_percentage"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:calendar-clock",
    ),
    # Voice balance
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid"),
        translation_key="voice_balance",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_voice_balance"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("voice", {})
        .get("used_percentage")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "voice", "used_percentage"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(
            data, ["balance_aggregated", "voice"], default={}
        ),
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:phone",
    ),
    # SMS balance
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid"),
        translation_key="sms_balance",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_sms_balance"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance_aggregated", {})
        .get("sms", {})
        .get("used_percentage")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance_aggregated", "sms", "used_percentage"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(
            data, ["balance_aggregated", "sms"], default={}
        ),
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:message",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        translation_key="out_of_bundle_cost",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_out_of_bundle_cost"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance", {}).get("out_of_bundle_cost")
        is not None,
        value_fn=lambda data: safe_get(
            data, ["balance", "out_of_bundle_cost"], default=0
        ),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        icon="mdi:currency-eur",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="credit",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_credit"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("balance", {}).get("credit") is not None,
        value_fn=lambda data: safe_get(data, ["balance", "credit"], default=0),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        icon="mdi:currency-eur",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "fixed-internet", "data-only"),
        translation_key="product_info",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_product_info"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("product", {}).get("price") is not None,
        value_fn=lambda data: safe_get(data, ["product", "price"], default=0.0),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(data, ["product"], default={}),
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        icon="mdi:package-variant",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="sim_alias",
        unique_id_fn=lambda data: (
            (data.get("sim") or {}).get("msisdn", "") + "_sim_alias"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("sim", {}).get("alias") is not None,
        value_fn=lambda data: safe_get(data, ["sim", "alias"], default=""),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(data, ["sim"], default={}),
        icon="mdi:sim",
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        translation_key="modem",
        subscription_types=("fixed-internet"),
        unique_id_fn=lambda data: (data.get("id", "") + "_modem_settings"),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data: data.get("modem_settings") is not None,
        value_fn=lambda data: safe_get(
            data, ["modem_settings", "actual", "gateway", "mode"], default=""
        ),
        device_name_fn=lambda data: "Fixed Internet",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: to_title_case_with_spaces(
            safe_get(
                data, ["installation", "modem", "modem_type"], default="Unknown Product"
            )
        )
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data: safe_get(data, ["modem_settings"], default={}),
        icon="mdi:router-network-wireless",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MobileVikings sensors."""
    _LOGGER.debug("[sensor|async_setup_entry|async_add_entities|start]")
    coordinator: MobileVikingsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities: list[MobileVikingsSensor] = []

    # Add static sensors from SENSOR_TYPES
    for sensor_type in SENSOR_TYPES:
        _LOGGER.debug(f"Searching for {sensor_type.key}-{sensor_type.translation_key}")
        if sensor_type.key in coordinator.data:
            entities.append(MobileVikingsSensor(coordinator, sensor_type, entry, None))

    for subscription_id, subscription_data in coordinator.data.get(
        "subscriptions", []
    ).items():
        # Add static sensors from SUBSCRIPTION_SENSOR_TYPES
        for sensor_type in SUBSCRIPTION_SENSOR_TYPES:
            _LOGGER.debug(
                f"Searching for {sensor_type.key}-{sensor_type.translation_key}"
            )
            # Check if the sensor applies to this subscription type
            if (
                sensor_type.subscription_types is None
                or subscription_data["type"] in sensor_type.subscription_types
            ):
                if sensor_type.key in coordinator.data:
                    entities.append(
                        MobileVikingsSensor(
                            coordinator, sensor_type, entry, subscription_id
                        )
                    )

    async_add_entities(entities)
    return


class MobileVikingsSensor(MobileVikingsEntity, RestoreSensor, SensorEntity):
    """Representation of an MobileVikings sensor."""

    entity_description: MobileVikingsSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MobileVikingsDataUpdateCoordinator,
        description: EntityDescription,
        entry: ConfigEntry,
        idx: int,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, idx)
        # Use the prefix from the description if provided, otherwise use the configuration title
        if hasattr(description, "entity_id_prefix_fn") and callable(
            description.entity_id_prefix_fn
        ):
            entity_id_prefix = description.entity_id_prefix_fn(self.item)
        else:
            entity_id_prefix = entry.title
        self.idx = idx
        self.entity_id = f"sensor.{DOMAIN}_{slugify(entity_id_prefix)}_{description.unique_id_fn(self.item)}"
        self._value: StateType = None

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(self.item)
        return self._value

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""

        await super().async_added_to_hass()
        if self.coordinator.data is None:
            sensor_data = await self.async_get_last_sensor_data()
            if sensor_data is not None:
                _LOGGER.debug(f"Restoring latest data for {self.entity_id}")
                self._value = sensor_data.native_value
            else:
                _LOGGER.debug(
                    f"Restoring latest - waiting for coordinator refresh {self.entity_id}"
                )
                await self.coordinator.async_request_refresh()
        else:
            self._value = self.entity_description.value_fn(self.item)

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
            and self.entity_description.attributes_fn(self.item) is not None
        ):
            return attributes | self.entity_description.attributes_fn(self.item)
        return attributes
