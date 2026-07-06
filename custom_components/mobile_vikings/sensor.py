"""Mobile Vikings / Jim Mobile sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

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
from .const import DOMAIN, JIM_MOBILE, MOBILE_VIKINGS
from .entity import MobileVikingsEntity
from .utils import safe_get, to_title_case_with_spaces

_LOGGER = logging.getLogger(__name__)


@dataclass
class MobileVikingsSensorDescription(SensorEntityDescription):
    """Sensor entity description for MobileVikings bundles."""

    available_fn: Callable[[dict, str | None], bool] | None = None
    value_fn: Callable[[dict, str | None], Any] | None = None
    attributes_fn: Callable[[dict, str | None], dict] | None = None
    unique_id_fn: Callable[[dict, str | None], dict] | None = None
    device_name_fn: Callable[[dict], str] | None = None
    device_identifier_fn: Callable[[dict], str] | None = None
    entity_id_prefix_fn: Callable[[dict], str] | None = None
    model_fn: Callable[[dict], str] | None = None
    translation_placeholders_fn: Callable[[dict, str | None], dict[str, str]] | None = (
        None
    )
    translation_key: str | None = None
    bundle_category: str | None = None
    subscription_types: tuple[str, ...] | None = None
    mobile_platforms: tuple[str, ...] | None = None
    bundle_type: str | None = None


SENSOR_TYPES: tuple[MobileVikingsSensorDescription, ...] = (
    MobileVikingsSensorDescription(
        key="customer_info",
        translation_key="customer_info",
        unique_id_fn=lambda data, _: "customer_info",
        icon="mdi:face-man",
        available_fn=lambda data, _: data.get("first_name") is not None,
        value_fn=lambda data, _: data.get("first_name"),
        device_name_fn=lambda data: "Customer",
        device_identifier_fn=lambda data: "Customer",
        model_fn=lambda data: "Customer Info",
        attributes_fn=lambda data, _: data,
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_available",
        unique_id_fn=lambda data, _: "loyalty_points_available",
        icon="mdi:currency-eur",
        available_fn=lambda data, _: data is not None
        and data.get("available") is not None,
        value_fn=lambda data, _: 0 if data is None else data.get("available", 0),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_blocked",
        unique_id_fn=lambda data, _: "loyalty_points_blocked",
        icon="mdi:currency-eur-off",
        available_fn=lambda data, _: data is not None
        and data.get("blocked") is not None,
        value_fn=lambda data, _: 0 if data is None else data.get("blocked", 0),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="loyalty_points_balance",
        translation_key="loyalty_points_pending",
        unique_id_fn=lambda data, _: "loyalty_points_pending",
        icon="mdi:timer-sand",
        available_fn=lambda data, _: data is not None
        and data.get("pending") is not None,
        value_fn=lambda data, _: 0 if data is None else data.get("pending", 0),
        device_name_fn=lambda data: "Loyalty Points",
        device_identifier_fn=lambda data: "Loyalty Points",
        model_fn=lambda data: "Loyalty Points",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="paid_invoices",
        translation_key="paid_invoices",
        unique_id_fn=lambda data, _: "paid_invoices",
        icon="mdi:receipt-text-check",
        available_fn=lambda data, _: data is not None
        and data.get("results") is not None,
        value_fn=lambda data, _: 0 if data is None else data.get("total_items", 0),
        device_name_fn=lambda data: "Invoices",
        device_identifier_fn=lambda data: "Invoices",
        model_fn=lambda data: "Invoices",
        attributes_fn=lambda data, _: {
            "invoices": safe_get(data, ["results"], default=[])
        },
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="unpaid_invoices",
        translation_key="unpaid_invoices",
        unique_id_fn=lambda data, _: "unpaid_invoices",
        icon="mdi:currency-eur",
        available_fn=lambda data, _: data is not None
        and data.get("results") is not None,
        value_fn=lambda data, _: sum(
            item.get("amount_due", 0) for item in data.get("results", [])
        ),
        device_name_fn=lambda data: "Invoices",
        device_identifier_fn=lambda data: "Invoices",
        model_fn=lambda data: "Invoices",
        attributes_fn=lambda data, _: {
            "invoices": safe_get(data, ["results"], default=[])
        },
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="unpaid_invoices",
        translation_key="next_invoice_expiration",
        unique_id_fn=lambda data, _: "next_invoice_expiration",
        icon="mdi:calendar-star",
        available_fn=lambda data, _: data is not None
        and data.get("results") is not None,
        value_fn=lambda data, _: min(
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
        attributes_fn=lambda data, _: {
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
        mobile_platforms=(MOBILE_VIKINGS),
    ),
)

SUBSCRIPTION_SENSOR_TYPES: tuple[MobileVikingsSensorDescription, ...] = (
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="credit",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_credit"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: safe_get(data, ["balance", "credit"], default=None)
        is not None,
        value_fn=lambda data, _: safe_get(data, ["balance", "credit"], default=0),
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
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "fixed-internet", "data-only"),
        translation_key="product_info",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_product_info"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: safe_get(data, ["product", "price"], default=None)
        is not None,
        value_fn=lambda data, _: safe_get(data, ["product", "price"], default=0.0),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, _: safe_get(data, ["product"], default={}),
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        icon="mdi:package-variant",
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        subscription_types=("postpaid", "prepaid", "data-only"),
        translation_key="sim_alias",
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_sim_alias"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: safe_get(data, ["sim", "alias"], default=None)
        is not None,
        value_fn=lambda data, _: safe_get(data, ["sim", "alias"], default=""),
        device_name_fn=lambda data: "Subscription",
        device_identifier_fn=lambda data: "Subscription " + data.get("id", ""),
        model_fn=lambda data: (data.get("sim") or {}).get("msisdn", "")
        + " - "
        + safe_get(
            data, ["product", "descriptions", "title"], default="Unknown Product"
        ),
        attributes_fn=lambda data, _: safe_get(data, ["sim"], default={}),
        icon="mdi:sim",
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        translation_key="modem",
        subscription_types=("fixed-internet"),
        unique_id_fn=lambda data, _: (data.get("id", "") + "_modem_settings"),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: data.get("modem_settings") is not None,
        value_fn=lambda data, _: safe_get(
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
        attributes_fn=lambda data, _: safe_get(data, ["modem_settings"], default={}),
        icon="mdi:router-network-wireless",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        translation_key="out_of_bundle_cost",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data, _: (
            (data.get("sim") or {}).get("msisdn", "") + "_out_of_bundle_cost"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, _: safe_get(
            data, ["balance", "out_of_bundle_cost"], default=None
        )
        is not None,
        value_fn=lambda data, _: safe_get(
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
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
)

BUNDLE_SENSOR_TYPES: tuple[MobileVikingsSensorDescription, ...] = (
    # Used percentage
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        translation_key="data_balance",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_used_percentage"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "used_percentage"], default=0
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
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:signal-4g",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        translation_key="data_remaining",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_data_remaining"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_gb"], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_gb"], default=0
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
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        icon="mdi:signal-4g",
        suggested_display_precision=1,
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        translation_key="remaining_days",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_remaining_days"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_days"], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_days"], default=0
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
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:calendar-end-outline",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="data",
        bundle_category="all",
        translation_key="period_percentage",
        subscription_types=("postpaid", "prepaid", "data-only"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "")
            + f"_{bundle_id}_period_percentage"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "period_percentage"], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "period_percentage"], default=0
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
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:calendar-clock",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="voice",
        bundle_category="all",
        translation_key="voice_balance",
        subscription_types=("postpaid", "prepaid"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_used_percentage"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "used_percentage"], default=0
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
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:phone",
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="voice",
        translation_key="period_percentage",
        subscription_types=("postpaid", "prepaid"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "")
            + f"_{bundle_id}_period_percentage"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "period_percentage"], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "period_percentage"], default=0
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
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:calendar-clock",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="voice",
        translation_key="remaining_days",
        subscription_types=("postpaid", "prepaid"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_remaining_days"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_days"], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "remaining_days"], default=0
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
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:calendar-end-outline",
        mobile_platforms=(MOBILE_VIKINGS),
    ),
    MobileVikingsSensorDescription(
        key="subscriptions",
        bundle_type="sms",
        bundle_category="all",
        translation_key="sms_balance",
        subscription_types=("postpaid", "prepaid"),
        unique_id_fn=lambda data, bundle_id: (
            (data.get("sim") or {}).get("msisdn", "") + f"_{bundle_id}_used_percentage"
        ),
        entity_id_prefix_fn=lambda data: "",
        available_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id], default=None
        )
        is not None,
        value_fn=lambda data, bundle_id: safe_get(
            data, ["balance", "bundles", bundle_id, "used_percentage"], default=0
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
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        icon="mdi:message",
        mobile_platforms=(MOBILE_VIKINGS, JIM_MOBILE),
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
    mobile_platform = coordinator.client.mobile_platform

    # Add static sensors from SENSOR_TYPES
    for sensor_type in SENSOR_TYPES:
        if mobile_platform not in sensor_type.mobile_platforms:
            _LOGGER.debug(
                f"Skipping {sensor_type.key}-{sensor_type.translation_key} for mobile platform {mobile_platform}"
            )
            continue
        _LOGGER.debug(f"Searching for {sensor_type.key}-{sensor_type.translation_key}")
        if sensor_type.key in coordinator.data:
            entities.append(
                MobileVikingsSensor(coordinator, sensor_type, entry, None, None)
            )

    # Add subscription-related sensors
    for subscription_id, subscription_data in coordinator.data.get(
        "subscriptions", {}
    ).items():
        # Existing static subscription sensors
        for sensor_type in SUBSCRIPTION_SENSOR_TYPES:
            if mobile_platform not in sensor_type.mobile_platforms:
                continue
            if (
                sensor_type.subscription_types is None
                or subscription_data["type"] in sensor_type.subscription_types
            ):
                if sensor_type.key in coordinator.data:
                    entities.append(
                        MobileVikingsSensor(
                            coordinator, sensor_type, entry, subscription_id, None
                        )
                    )

        bundles = subscription_data.get("balance", {}).get("bundles", {})
        if isinstance(bundles, list):
            bundles = {
                f"{b.get('type', 'unknown')}_{b.get('category', 'unknown')}": b
                for b in bundles
            }
        for bundle_id, bundle in bundles.items():
            bundle_type = bundle.get("type")
            for sensor_type in BUNDLE_SENSOR_TYPES:
                if bundle_type != "default" and sensor_type.bundle_category is None:
                    continue
                if mobile_platform not in sensor_type.mobile_platforms:
                    continue
                if (
                    sensor_type.subscription_types is None
                    or subscription_data["type"] in sensor_type.subscription_types
                ):
                    if sensor_type.bundle_type == bundle_type:
                        entities.append(
                            MobileVikingsSensor(
                                coordinator,
                                sensor_type,
                                entry,
                                subscription_id,
                                bundle_id,
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
        bundle_id: str,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, idx, bundle_id)
        # Use the prefix from the description if provided, otherwise use the configuration title
        if hasattr(description, "entity_id_prefix_fn") and callable(
            description.entity_id_prefix_fn
        ):
            prefix = slugify(description.entity_id_prefix_fn(self.item))
        else:
            prefix = slugify(entry.title)

        # Clean up entity ID construction to avoid double underscores
        entity_id_prefix = f"_{prefix}" if prefix else ""
        self.entity_id = f"sensor.{DOMAIN}{entity_id_prefix}_{description.unique_id_fn(self.item, self.bundle_id)}"
        if hasattr(description, "translation_placeholders_fn") and callable(
            description.translation_placeholders_fn
        ):
            self._attr_translation_placeholders = (
                description.translation_placeholders_fn(self.item, self.bundle_id)
            )
        self._value: StateType = None

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(self.item, self.bundle_id)
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
            self._value = self.entity_description.value_fn(self.item, self.bundle_id)

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}

        attributes = {"last_synced": self.last_synced}

        if self.entity_description.attributes_fn:
            bundle_id = getattr(self, "bundle_id", None)
            extra_attrs = self.entity_description.attributes_fn(self.item, bundle_id)
            if extra_attrs:
                return attributes | extra_attrs

        return attributes
