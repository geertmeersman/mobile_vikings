"""Config flow to configure the MobileVikings integration."""
from abc import ABC
from abc import abstractmethod
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import ConfigFlow
from homeassistant.config_entries import OptionsFlow
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowHandler
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import TextSelector
from homeassistant.helpers.selector import TextSelectorConfig
from homeassistant.helpers.selector import TextSelectorType
from homeassistant.helpers.typing import UNDEFINED

from .client import MobileVikingsClient
from .const import DOMAIN
from .const import NAME
from .exceptions import BadCredentialsException
from .exceptions import MobileVikingsServiceException
from .models import MobileVikingsConfigEntryData
from .utils import log_debug

DEFAULT_ENTRY_DATA = MobileVikingsConfigEntryData(
    username=None,
    password=None,
)


class MobileVikingsCommonFlow(ABC, FlowHandler):
    """Base class for MobileVikings flows."""

    def __init__(self, initial_data: MobileVikingsConfigEntryData) -> None:
        """Initialize MobileVikingsCommonFlow."""
        self.initial_data = initial_data
        self.new_entry_data = MobileVikingsConfigEntryData()
        self.new_title: str | None = None

    @abstractmethod
    def finish_flow(self) -> FlowResult:
        """Finish the flow."""

    def new_data(self):
        """Construct new data."""
        return DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data

    async def async_validate_input(self, user_input: dict[str, Any]) -> None:
        """Validate user credentials."""

        client = MobileVikingsClient(
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
        )

        profile = await self.hass.async_add_executor_job(client.login)

        return profile

    async def async_step_connection_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle connection configuration."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_title = user_input[CONF_USERNAME]
                self.new_entry_data |= user_input
                await self.async_set_unique_id(f"{DOMAIN}_" + user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                log_debug(f"New account {self.new_title} added")
                return self.finish_flow()
            errors = test["errors"]
        fields = {
            vol.Required(CONF_USERNAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
        }
        return self.async_show_form(
            step_id="connection_init",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def test_connection(self, user_input: dict | None = None) -> dict:
        """Test the connection to MobileVikings."""
        errors: dict = {}
        profile: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            try:
                profile = await self.async_validate_input(user_input)
            except AssertionError as exception:
                errors["base"] = "cannot_connect"
                log_debug(f"[async_step_password|login] AssertionError {exception}")
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except MobileVikingsServiceException:
                errors["base"] = "service_error"
            except BadCredentialsException:
                errors["base"] = "invalid_auth"
            except Exception as exception:
                errors["base"] = "unknown"
                log_debug(exception)
        return {"profile": profile, "errors": errors}

    async def async_step_password(self, user_input: dict | None = None) -> FlowResult:
        """Configure password."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_entry_data |= MobileVikingsConfigEntryData(
                    password=user_input[CONF_PASSWORD],
                )
                log_debug(
                    f"Password changed for {test['user_details'].get('customer_number')}"
                )
                return self.finish_flow()

        fields = {
            vol.Required(CONF_PASSWORD): cv.string,
        }
        return self.async_show_form(
            step_id="password",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields),
                self.initial_data
                | MobileVikingsConfigEntryData(
                    password=None,
                ),
            ),
            errors=errors,
        )


class MobileVikingsOptionsFlow(MobileVikingsCommonFlow, OptionsFlow):
    """Handle MobileVikings options."""

    general_settings: dict

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize MobileVikings options flow."""
        self.config_entry = config_entry
        super().__init__(initial_data=config_entry.data)  # type: ignore[arg-type]

    @callback
    def finish_flow(self) -> FlowResult:
        """Update the ConfigEntry and finish the flow."""
        new_data = DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
            title=self.new_title or UNDEFINED,
        )
        return self.async_create_entry(title="", data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage MobileVikings options."""
        return self.async_show_menu(
            step_id="options_init",
            menu_options=[
                "password",
            ],
        )


class MobileVikingsConfigFlow(MobileVikingsCommonFlow, ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MobileVikings."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize MobileVikings Config Flow."""
        super().__init__(initial_data=DEFAULT_ENTRY_DATA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MobileVikingsOptionsFlow:
        """Get the options flow for this handler."""
        return MobileVikingsOptionsFlow(config_entry)

    @callback
    def finish_flow(self) -> FlowResult:
        """Create the ConfigEntry."""
        title = self.new_title or NAME
        return self.async_create_entry(
            title=title,
            data=DEFAULT_ENTRY_DATA | self.new_entry_data,
        )

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_connection_init()
