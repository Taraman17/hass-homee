"""Config flow for homee integration."""

import logging

from pyHomee import (
    HomeeAuthFailedException as HomeeAuthenticationFailedException,
    HomeeConnectionFailedException,
    Homee,
)
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_ADD_HOMEE_DATA,
    CONF_ALL_DEVICES,
    CONF_DOOR_GROUPS,
    CONF_GROUPS,
    CONF_IMPORT_GROUPS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

default_options = {
    "import_all_devices": True,
    "add_homee_data": False,
}

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_ALL_DEVICES, default="all"): SelectSelector(
            SelectSelectorConfig(
                options=["all", "groups"],
                translation_key="all_devices_or_groups",
                multiple=False,
            )
        ),
        vol.Required(
            CONF_ADD_HOMEE_DATA,
            default=default_options.get(CONF_ADD_HOMEE_DATA),
        ): bool,
    }
)


async def validate_and_connect(hass: core.HomeAssistant, data) -> Homee:
    """Validate the user input allows us to connect."""

    # TODO DATA SCHEMA validation

    # Create a Homee object and try to receive an access token.
    # This tells us if the host is reachable and if the credentials work
    homee = Homee(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])

    try:
        await homee.get_access_token()
        _LOGGER.info("Got access token for homee")
    except HomeeAuthenticationFailedException as exc:
        _LOGGER.warning("Authentication to Homee failed: %s", exc.reason)
        raise InvalidAuth from exc
    except HomeeConnectionFailedException as exc:
        _LOGGER.warning("Connection to Homee failed: %s", exc.__cause__)
        raise CannotConnect from exc

    hass.loop.create_task(homee.run())
    _LOGGER.info("Homee task created")
    await homee.wait_until_connected()
    _LOGGER.info("Homee connected")
    homee.disconnect()
    _LOGGER.info("Homee disconnecting")
    await homee.wait_until_disconnected()
    _LOGGER.info("Homee config successfully tested")
    # Return homee instance
    return homee


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for homee."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler."""
        return OptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        # self.homee_host: str = None
        # self.homee_id: str = None
        self.homee: Homee = None
        self.all_devices: bool = True
        self.debug_data: bool = False

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""

        errors = {}
        if user_input is not None:
            try:
                self.homee = await validate_and_connect(self.hass, user_input)
                await self.async_set_unique_id(self.homee.settings.uid)
                self._abort_if_unique_id_configured()
                _LOGGER.info(
                    "Created new homee entry with ID %s", self.homee.settings.uid
                )
                self.all_devices = user_input[CONF_ALL_DEVICES] == "all"
                self.debug_data = user_input[CONF_ADD_HOMEE_DATA]
                return await self.async_step_groups()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except AbortFlow:
                return self.async_abort(reason="already_configured")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_SCHEMA,
            errors=errors,
        )

    async def async_step_groups(self, user_input=None):
        """Configure groups options."""
        groups = [str(g.id) for g in self.homee.groups]
        groups_selection = {
            str(g.id): f"{g.name} ({len(g.nodes)})" for g in self.homee.groups
        }

        # There doesn't seem to be a way to disable a field - so we need 2 seperate versions.
        if self.all_devices:
            # Omit the first option if we import all devices.
            GROUPS_SCHEMA = vol.Schema(
                {
                    vol.Required(
                        CONF_WINDOW_GROUPS,
                        default=[],
                    ): cv.multi_select(groups_selection),
                    vol.Required(
                        CONF_DOOR_GROUPS,
                        default=[],
                    ): cv.multi_select(groups_selection),
                }
            )
        else:
            GROUPS_SCHEMA = vol.Schema(
                {
                    vol.Required(
                        CONF_IMPORT_GROUPS,
                        default=groups,
                    ): cv.multi_select(groups_selection),
                    vol.Required(
                        CONF_WINDOW_GROUPS,
                        default=[],
                    ): cv.multi_select(groups_selection),
                    vol.Required(
                        CONF_DOOR_GROUPS,
                        default=[],
                    ): cv.multi_select(groups_selection),
                }
            )

        if user_input is not None:
            return self.async_create_entry(
                title=f"{self.homee.settings.uid} ({self.homee.host})",
                data={
                    CONF_HOST: self.homee.host,
                    CONF_USERNAME: self.homee.user,
                    CONF_PASSWORD: self.homee.password,
                },
                options={
                    CONF_ALL_DEVICES: self.all_devices,
                    CONF_ADD_HOMEE_DATA: self.debug_data,
                    CONF_GROUPS: user_input,
                },
            )

        return self.async_show_form(step_id="groups", data_schema=GROUPS_SCHEMA)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Manage the options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Init the first step of the options flow."""
        homee: Homee = self.hass.data[DOMAIN][self.entry.entry_id]
        groups_selection = {
            str(g.id): f"{g.name} ({len(g.nodes)})" for g in homee.groups
        }

        # TODO: Add support for changing imported devices.
        CONFIG_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_WINDOW_GROUPS,
                    default=self.entry.options[CONF_GROUPS][CONF_WINDOW_GROUPS],
                ): cv.multi_select(groups_selection),
                vol.Required(
                    CONF_DOOR_GROUPS,
                    default=self.entry.options[CONF_GROUPS][CONF_DOOR_GROUPS],
                ): cv.multi_select(groups_selection),
                vol.Required(
                    CONF_ADD_HOMEE_DATA,
                    default=self.entry.options[CONF_ADD_HOMEE_DATA],
                ): bool,
            }
        )

        if user_input is not None:
            input_data = {}
            input_data[CONF_ALL_DEVICES] = self.entry.options[CONF_ALL_DEVICES]
            input_data[CONF_GROUPS] = {}
            input_data[CONF_GROUPS][CONF_IMPORT_GROUPS] = self.entry.options[
                CONF_GROUPS
            ].get(CONF_IMPORT_GROUPS, [])
            input_data[CONF_GROUPS][CONF_WINDOW_GROUPS] = user_input[CONF_WINDOW_GROUPS]
            input_data[CONF_GROUPS][CONF_DOOR_GROUPS] = user_input[CONF_DOOR_GROUPS]
            input_data[CONF_ADD_HOMEE_DATA] = user_input[CONF_ADD_HOMEE_DATA]
            return self.async_create_entry(title="", data=input_data)

        return self.async_show_form(step_id="init", data_schema=CONFIG_SCHEMA)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
