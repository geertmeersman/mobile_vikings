"""Base MobileVikings entity."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import MobileVikingsDataUpdateCoordinator
from .const import ATTRIBUTION, DOMAIN, NAME, VERSION, WEBSITE

_LOGGER = logging.getLogger(__name__)


class MobileVikingsEntity(CoordinatorEntity[MobileVikingsDataUpdateCoordinator]):
    """Base MobileVikings entity."""

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset(
        {
            "invoices",
            "last_synced",
        }
    )

    def __init__(
        self,
        coordinator: MobileVikingsDataUpdateCoordinator,
        description: EntityDescription,
        idx: int,
    ) -> None:
        """Initialize MobileVikings entities."""
        super().__init__(coordinator)
        self.idx = idx
        self.entity_description = description
        self._identifier = f"{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{coordinator.config_entry.entry_id}-{self.entity_description.device_identifier_fn(self.item)}",
                )
            },
            name=self.entity_description.device_name_fn(self.item),
            translation_key=slugify(self.entity_description.device_name_fn(self.item)),
            manufacturer=NAME,
            configuration_url=WEBSITE,
            entry_type=DeviceEntryType.SERVICE,
            model=self.entity_description.model_fn(self.item),
            sw_version=VERSION,
        )
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self.entity_description.unique_id_fn(self.item)}"
        self.last_synced = datetime.now()
        _LOGGER.debug(f"[MobileVikingsEntity|init] {self._attr_unique_id}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if len(self.coordinator.data):
            self.last_synced = datetime.now()
            self.async_write_ha_state()
            return
        _LOGGER.debug(
            f"[MobileVikingsEntity|_handle_coordinator_update] {self._attr_unique_id}: async_write_ha_state ignored since API fetch failed or not found",
            True,
        )

    @property
    def item(self) -> dict:
        """Return the data for this entity."""
        try:
            if self.idx is not None:
                return self.coordinator.data[self.entity_description.key][self.idx]
            return self.coordinator.data[self.entity_description.key]
        except (KeyError, IndexError):
            _LOGGER.error("Data not available for entity %s", self._attr_unique_id)
            return {}

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return super().available and self.entity_description.available_fn(self.item)

    async def async_update(self) -> None:
        """Update the entity.  Only used by the generic entity update service."""
        return
