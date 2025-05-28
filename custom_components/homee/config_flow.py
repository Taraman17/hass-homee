"""Config flow for homee integration."""

import logging
from typing import Any

from pyHomee import (
    HomeeAuthFailedException as HomeeAuthenticationFailedException,
    HomeeConnectionFailedException,
    Homee,
)
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
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


class HomeeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for homee."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    homee: Homee

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""

        errors = {}
        if user_input is not None:
            self.homee = Homee(
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                await self.homee.get_access_token()
            except HomeeConnectionFailedException:
                errors["base"] = "cannot_connect"
            except HomeeAuthenticationFailedException:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                _LOGGER.info("Got access token for homee")
                self.hass.loop.create_task(self.homee.run())
                _LOGGER.debug("Homee task created")
                await self.homee.wait_until_connected()
                _LOGGER.info("Homee connected")
                self.homee.disconnect()
                _LOGGER.debug("Homee disconnecting")
                await self.homee.wait_until_disconnected()
                _LOGGER.info("Homee config successfully tested")

                await self.async_set_unique_id(self.homee.settings.uid)

                self._abort_if_unique_id_configured()

                _LOGGER.info(
                    "Created new homee entry with ID %s", self.homee.settings.uid
                )

                return self.async_create_entry(
                    title=f"{self.homee.settings.homee_name} ({self.homee.host})",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reconfigure flow."""
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry()
        new_data = reconfigure_entry.data.copy()
        suggested_values = {
            CONF_HOST: new_data.get(CONF_HOST),
            CONF_USERNAME: new_data.get(CONF_USERNAME),
            CONF_PASSWORD: new_data.get(CONF_PASSWORD),
        }

        if user_input:
            try:
                self.homee = await validate_and_connect(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(self.homee.settings.uid)

                new_data[CONF_HOST] = user_input.get(CONF_HOST)
                new_data[CONF_USERNAME] = user_input.get(CONF_USERNAME)
                new_data[CONF_PASSWORD] = user_input.get(CONF_PASSWORD)

                _LOGGER.info("Updated homee entry with ID %s", self.homee.settings.uid)
                return self.async_update_reload_and_abort(
                    reconfigure_entry, data=new_data
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                AUTH_SCHEMA, suggested_values
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
