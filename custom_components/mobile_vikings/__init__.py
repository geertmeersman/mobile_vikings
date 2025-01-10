"""MobileVikings integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.storage import STORAGE_DIR, Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import MobileVikingsClient
from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MobileVikings from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    for platform in PLATFORMS:
        hass.data[DOMAIN][entry.entry_id].setdefault(platform, set())

    client = MobileVikingsClient(
        hass=hass,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
    if storage_dir.is_file():
        storage_dir.unlink()
    storage_dir.mkdir(exist_ok=True)
    store: Store = Store(hass, 1, f"{DOMAIN}/{entry.entry_id}")
    dev_reg = dr.async_get(hass)

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator = (
        MobileVikingsDataUpdateCoordinator(
            hass,
            entry=entry,
            client=client,
            dev_reg=dev_reg,
            store=store,
        )
    )
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_trigger_cleanup()

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of pubsub subscriptions created during config flow."""

    # Define blocking file operations
    def remove_storage_files():
        storage = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}/{entry.entry_id}")
        storage.unlink(missing_ok=True)  # Unlink (delete) the storage file

        storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
        # If the directory exists and is empty, remove it
        if storage_dir.is_dir() and not any(storage_dir.iterdir()):
            storage_dir.rmdir()

    # Offload the file system operations to a thread
    await hass.async_add_executor_job(remove_storage_files)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload the platforms first
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Define blocking file operations
        def remove_storage_files():
            storage = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}/{entry.entry_id}")
            storage.unlink(missing_ok=True)  # Unlink (delete) the storage file

            storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
            # If the directory exists and is empty, remove it
            if storage_dir.is_dir() and not any(storage_dir.iterdir()):
                storage_dir.rmdir()

        # Offload the file system operations to a thread
        await hass.async_add_executor_job(remove_storage_files)

    return unload_ok


class MobileVikingsDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for MobileVikings."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MobileVikingsClient,
        dev_reg: dr.DeviceRegistry,
        store: Store,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self._debug = _LOGGER.isEnabledFor(logging.DEBUG)
        self._init = True
        self._config_entry_id = entry
        self._device_registry = dev_reg
        self.client = client
        self.hass = hass
        self.store = store
        self.entry = entry

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time when a config entry is setup."""
        self.data = await self.store.async_load() or {}
        await super().async_config_entry_first_refresh()

    async def get_data(self) -> dict | None:
        """Get the data from the Robonect client."""
        data = await self.client.get_data()
        if self._init:
            self._init = False
        for key, value in data.items():
            # Check if the value is a dictionary and contains an "error" key
            if isinstance(value, dict) and value.get("error"):
                if self._debug:
                    _LOGGER.debug(
                        "Skipping key %s due to error: %s", key, value.get("error")
                    )
                continue  # Skip this key if "error" is present
            self.data[key] = value
        await self.store.async_save(self.data)

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        if self._debug:
            await self.get_data()
            if self.data:
                _LOGGER.debug(f"Returned items: {self.data}")

        try:
            await self.get_data()
        except Exception as exception:
            _LOGGER.warning(f"Exception {exception}")

        if len(self.data) > 0:
            return self.data
        return {}

    async def async_trigger_cleanup(self) -> None:
        """Trigger entity cleanup."""
        entity_reg: er.EntityRegistry = er.async_get(self.hass)
        ha_entity_reg_list: list[er.RegistryEntry] = er.async_entries_for_config_entry(
            entity_reg, self.entry.entry_id
        )

        for entry in ha_entity_reg_list:
            # Check if the entity starts with any base entity ID or if it's restored
            entity_state = self.hass.states.get(entry.entity_id)
            if entity_state is not None:
                continue
            _LOGGER.info("Removing entity: %s", entry.entity_id)
            entity_reg.async_remove(entry.entity_id)
        self._async_remove_empty_devices(entity_reg)

    @callback
    def _async_remove_empty_devices(self, entity_reg: er.EntityRegistry) -> None:
        """Remove devices with no entities."""

        device_reg = dr.async_get(self.hass)
        device_list = dr.async_entries_for_config_entry(device_reg, self.entry.entry_id)
        for device_entry in device_list:
            if not er.async_entries_for_device(
                entity_reg,
                device_entry.id,
                include_disabled_entities=True,
            ):
                _LOGGER.info("Removing device: %s", device_entry.name)
                device_reg.async_remove_device(device_entry.id)
