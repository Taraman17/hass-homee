"""The homee integration."""

import logging

from pyHomee import Homee
from pyHomee.const import NodeProfile
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ATTRIBUTE,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_NODE,
    ATTR_VALUE,
    CONF_ALL_DEVICES,
    CONF_DOOR_GROUPS,
    CONF_GROUPS,
    CONF_IMPORT_GROUPS,
    CONF_INITIAL_OPTIONS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
    SERVICE_SET_VALUE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "climate",
    "cover",
    "event",
    "light",
    "lock",
    "number",
    "sensor",
    "switch",
]

type HomeeConfigEntry = ConfigEntry[Homee]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the homee component."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Register the set_value service that can be used
    # for debugging and custom automations.
    SET_VALUE_SCHEMA = vol.Schema(
        {
            vol.Required(ATTR_CONFIG_ENTRY_ID): str,
            vol.Required(ATTR_NODE): int,
            vol.Required(ATTR_ATTRIBUTE): int,
            vol.Required(ATTR_VALUE): vol.Any(int, float, str),
        }
    )

    async def async_handle_set_value(call: ServiceCall):
        """Handle the set value service call."""

        if not (
            entry := hass.config_entries.async_get_entry(
                call.data[ATTR_CONFIG_ENTRY_ID]
            )
        ):
            raise ServiceValidationError("Entry not found")
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError("Entry not loaded")
        homee: Homee = entry.runtime_data

        node = call.data.get(ATTR_NODE, 0)
        attribute = call.data.get(ATTR_ATTRIBUTE, 0)
        value = call.data.get(ATTR_VALUE, 0)

        await homee.set_value(node, attribute, value)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_VALUE, async_handle_set_value, SET_VALUE_SCHEMA
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: HomeeConfigEntry) -> bool:
    """Set up homee from a config entry."""
    # Create the Homee api object using host, user,
    # password & pyHomee instance from the config
    homee = Homee(
        host=entry.data[CONF_HOST],
        user=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        device="pymee_" + hass.config.location_name,
        reconnect_interval=10,
        max_retries=100,
    )

    # Start the homee websocket connection as a new task
    # and wait until we are connected
    hass.loop.create_task(homee.run())
    await homee.wait_until_connected()

    # Migrate unique ids that are int.
    await _migrate_old_unique_ids(hass, entry.entry_id)

    # Log info about nodes, to facilitate recognition of unknown nodes.
    for node in homee.nodes:
        _LOGGER.info(
            "Found node %s, with following Data: %s",
            node.name,
            node.raw_data,
        )

    entry.runtime_data = homee

    # create device register entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={
            (dr.CONNECTION_NETWORK_MAC, dr.format_mac(homee.settings.mac_address))
        },
        identifiers={(DOMAIN, homee.settings.uid)},
        manufacturer="homee",
        name=homee.settings.homee_name,
        model="homee",
        sw_version=homee.settings.version,
        hw_version="TBD",
    )

    # Forward entry setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: HomeeConfigEntry) -> bool:
    """Unload a homee config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get Homee object and remove it from data
        homee: Homee = entry.runtime_data

        # Schedule homee disconnect
        homee.disconnect()

        # Remove services
        hass.services.async_remove(DOMAIN, SERVICE_SET_VALUE)

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload homee integration after config change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    homee = config_entry.runtime_data
    model = NodeProfile[device_entry.model.upper()].value
    for node in homee.nodes:
        # 'identifiers' is a set of tuples, so we need to check for the tuple.
        if ("homee", node.id) in device_entry.identifiers:
            if node.profile == model:
                # If Node is still present in Homee, don't delete.
                return False

    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version == 1:
        _LOGGER.debug("Migrating from version %s", config_entry.version)

        new_data = {**config_entry.data}

        # If for any reason the options are not set, use the initial_options.
        if config_entry.options.get(CONF_GROUPS) is not None:
            new_options = {**config_entry.options}
        else:
            new_options = {**config_entry.data[CONF_INITIAL_OPTIONS]}

        new_options[CONF_ALL_DEVICES] = False
        import_groups = new_options.pop(CONF_GROUPS, [])
        conf_groups = new_options[CONF_GROUPS] = {}
        conf_groups[CONF_IMPORT_GROUPS] = import_groups
        conf_groups[CONF_WINDOW_GROUPS] = new_options.pop(CONF_WINDOW_GROUPS, [])
        conf_groups[CONF_DOOR_GROUPS] = new_options.pop(CONF_DOOR_GROUPS, [])

        # Initial options are dropped in v2 since the options
        # can be changed later anyhow.
        del new_data[CONF_INITIAL_OPTIONS]

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, options=new_options, version=2
        )

        _LOGGER.info("Migration to v%s successful", config_entry.version)

    if config_entry.version == 2:
        _LOGGER.debug("Migrating from version %s", config_entry.version)

        new_data = {**config_entry.data}

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=3
        )

        _LOGGER.info("Migration to v%s successful", config_entry.version)

    return True

async def _migrate_old_unique_ids(hass: HomeAssistant, entry_id: str) -> None:
    entity_registry = er.async_get(hass)

    @callback
    def _async_migrator(entity_entry: er.RegistryEntry) -> dict[str, str] | None:
        # Climate entities had a string unique id.
        if isinstance(entity_entry.unique_id, int):
            new_unique_id = f"{entity_entry.unique_id}-climate"
            if existing_entity_id := entity_registry.async_get_entity_id(
                entity_entry.domain, entity_entry.platform, new_unique_id
            ):
                _LOGGER.error(
                    "Cannot migrate to unique_id '%s', already exists for '%s', "
                    "You may have to delete unavailable ring entities",
                    new_unique_id,
                    existing_entity_id,
                )
                return None
            _LOGGER.info("Fixing non string unique id %s", entity_entry.unique_id)
            return {"new_unique_id": new_unique_id}

        return None

    await er.async_migrate_entries(hass, entry_id, _async_migrator)
