"""Config flow for homee integration."""
import asyncio
import logging

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

# import homeassistant.helpers.config_validation as cv
from pymee import (
    AuthenticationFailedException as HomeeAuthenticationFailedException,
    Homee,
)
import voluptuous as vol

from .const import (
    CONF_ADD_HOMEE_DATA,
    CONF_ALL_DEVICES,
    CONF_DOOR_GROUPS,
    CONF_GROUPS,
    CONF_INITIAL_OPTIONS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = schema = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def get_options_schema(homee: Homee, default_options={}):
    """Returns the Schema for the options Dialog."""
    groups = [str(g.id) for g in homee.groups]
    groups_selection = {str(g.id): f"{g.name} ({len(g.nodes)})" for g in homee.groups}

    return vol.Schema(
        {
            vol.Required(
                CONF_GROUPS,
                default=default_options.get(CONF_GROUPS, groups),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_WINDOW_GROUPS,
                default=default_options.get(CONF_WINDOW_GROUPS, []),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_DOOR_GROUPS,
                default=default_options.get(CONF_DOOR_GROUPS, []),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_ADD_HOMEE_DATA,
                default=default_options.get(CONF_ADD_HOMEE_DATA, False),
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
        _LOGGER.info("got access token for homee")
    except HomeeAuthenticationFailedException as exc:
        raise InvalidAuth from exc
    except asyncio.TimeoutError as exc:
        raise CannotConnect from exc

    hass.loop.create_task(homee.run())
    _LOGGER.info("homee task created")
    await homee.wait_until_connected()
    _LOGGER.info("homee connected")
    homee.disconnect()
    _LOGGER.info("homee disconnecting")
    await homee.wait_until_disconnected()
    _LOGGER.info("homee config successfully tested")
    # Return homee instance
    return homee


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for homee."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    # CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.homee_host: str = None
        self.homee_id: str = None
        self.homee: Homee = None

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
                return await self.async_step_config1()
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
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_config1(self, user_input=None):
        """Configure initial options."""

        if user_input is not None:
            # self.init_info = user_input
            return await self.async_step_config2()

        config1_schema = vol.Schema(
            {
                vol.Required(CONF_ALL_DEVICES, default=True): SelectSelector(
                    SelectSelectorConfig(
                        translation_key="all_devices_or_groups", multiple=False
                    )
                )
            }
        )

        return self.async_show_form(step_id="config1", data_schema=config1_schema)

    async def async_step_config2(self, user_input=None):
        """Configure groups options."""

        if user_input is not None:
            return self.async_create_entry(
                title=f"{self.homee.settings.uid} ({self.homee.host})",
                data={
                    CONF_HOST: self.homee.host,
                    CONF_USERNAME: self.homee.user,
                    CONF_PASSWORD: self.homee.password,
                    CONF_INITIAL_OPTIONS: user_input,
                },
            )

        return self.async_show_form(
            step_id="config2", data_schema=get_options_schema(self.homee)
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Manage the options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        homee: Homee = self.hass.data[DOMAIN][self.entry.entry_id]

        return self.async_show_form(
            step_id="init", data_schema=get_options_schema(homee, self.entry.options)
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
