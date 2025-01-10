"""Models used by MobileVikings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class MobileVikingsConfigEntryData(TypedDict):
    """Config entry for the MobileVikings integration."""

    username: str | None
    password: str | None


@dataclass
class MobileVikingsEnvironment:
    """Class to describe a MobileVikings environment."""

    api_endpoint: str
    uwa_endpoint: str
    deals_endpoint: str
    authority: str
    logincheck: str


@dataclass
class MobileVikingsItem:
    """MobileVikings item model."""

    name: str = ""
    key: str = ""
    type: str = ""
    state: str = ""
    device_key: str = ""
    device_name: str = ""
    device_model: str = ""
    data: dict = field(default_factory=dict)
    extra_attributes: dict = field(default_factory=dict)
    native_unit_of_measurement: str = None
