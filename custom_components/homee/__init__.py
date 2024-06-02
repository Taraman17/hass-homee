"""The homee integration."""

import asyncio
import logging
import re

from pymee import Homee
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_ATTRIBUTE,
    ATTR_HOMEE_DATA,
    ATTR_NODE,
    ATTR_VALUE,
    CONF_ADD_HOMEE_DATA,
    CONF_ALL_DEVICES,
    CONF_DOOR_GROUPS,
    CONF_GROUPS,
    CONF_IMPORT_GROUPS,
    CONF_INITIAL_OPTIONS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
    SERVICE_SET_VALUE,
    SERVICE_UPDATE_ENTITY,
)
from .helpers import get_attribute_for_enum

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

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


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the homee component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up homee from a config entry."""
    # Create the Homee api object using host, user,
    # password & pymee instance from the config
    homee = Homee(
        host=entry.data[CONF_HOST],
        user=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        device="pymee_" + hass.config.location_name,
        reconnectInterval=10,
        maxRetries=100,
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
            node._data,
        )

    hass.data[DOMAIN][entry.entry_id] = homee

    # Register the set_value service that can be used
    # for debugging and custom automations.
    async def handle_set_value(call: ServiceCall):
        """Handle the service call."""

        try:
            node = int(call.data.get(ATTR_NODE, 0))
        except ValueError as exc:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_integer",
                translation_placeholders={"service_attr": "Node"},
            ) from exc

        try:
            attribute = int(call.data.get(ATTR_ATTRIBUTE, 0))
        except ValueError as exc:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_integer",
                translation_placeholders={"service_attr": "Attribute"},
            ) from exc

        try:
            value = float(call.data.get(ATTR_VALUE, 0))
        except ValueError as exc:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_float",
                translation_placeholders={"service_attr": "Value"},
            ) from exc

        hass.async_create_task(homee.set_value(node, attribute, value))

    hass.services.async_register(DOMAIN, SERVICE_SET_VALUE, handle_set_value)

    # Register the update_attribute service that can be used
    # for debugging and custom automations.
    async def handle_update_entity(call: ServiceCall):
        """Handle the service call."""
        if "entity_id" in call.data:
            entity_registry = er.async_get(hass)
            for entity in call.data["entity_id"]:
                this_entity = entity_registry.async_get(entity)
                matches = re.search(r"^(\d+)-\w+-(\d+)$", this_entity.unique_id)
                if matches is not None:
                    node_id, attribute_id = matches.group(1, 2)
                    hass.async_create_task(
                        homee.update_attribute(node_id, attribute_id)
                    )
                else:
                    matches = re.search(r"^(\d{1,4})-\w{1,20}", this_entity.unique_id)
                    node_id = matches.groups(1)
                    hass.async_create_task(homee.update_node(node_id))

        if "device_id" in call.data:
            for device_id in call.data["device_id"]:
                device_registry = dr.async_get(hass)
                device = device_registry.async_get(device_id)
                hass.async_create_task(
                    homee.update_node(list(device.identifiers)[0][1])
                )
        if "area_id" in call.data:
            for area_id in call.data["area_id"]:
                area_devices = dr.async_entries_for_area(dr.async_get(hass), area_id)
                for device in area_devices:
                    hass.async_create_task(
                        homee.update_node(list(device.identifiers)[0][1])
                    )

    hass.services.async_register(DOMAIN, SERVICE_UPDATE_ENTITY, handle_update_entity)

    # create device register entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        # TODO: figure out how to derive the MAC address -
        # will need to update pymee?
        # connections={(dr.CONNECTION_NETWORK_MAC, entry.mac)},
        identifiers={(DOMAIN, homee.deviceId)},
        manufacturer="homee",
        name=homee.settings.homee_name,
        model="homee",
        sw_version=homee.settings.version,
        hw_version="TBD",
    )

    # async_setup_devices(hass, homee, entry)

    # Forward entry setup to the platforms
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a homee config entry."""
    # Unload platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        # Get Homee object and remove it from data
        homee: Homee = hass.data[DOMAIN][entry.entry_id]
        hass.data[DOMAIN].pop(entry.entry_id)

        # Schedule homee disconnect
        homee.disconnect()

        # Remove services
        hass.services.async_remove(DOMAIN, SERVICE_SET_VALUE)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_ENTITY)

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload homee integration after config change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
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

        # initial options are dropped in v2 since the options
        # can be changed later anyhow.
        del new_data[CONF_INITIAL_OPTIONS]

        config_entry.version = 2
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, options=new_options
        )

        _LOGGER.info("Migration to v%s successful", config_entry.version)

    return True


class HomeeNodeEntity:
    """Representation of a Node in Homee."""

    _unrecorded_attributes = frozenset({ATTR_HOMEE_DATA})

    def __init__(self, node: HomeeNode, entity: Entity, entry: ConfigEntry) -> None:
        """Initialize the wrapper using a HomeeNode and target entity."""
        self._node = node
        self._entity = entity
        self._clear_node_listener = None
        self._attr_unique_id = node.id
        self._entry = entry

        self._homee_data = {
            "id": node.id,
            "name": node.name,
            "profile": node.profile,
            "attributes": [{"id": a.id, "type": a.type} for a in node.attributes],
        }

    async def async_added_to_hass(self) -> None:
        """Add the homee binary sensor device to home assistant."""
        self.register_listener()

    async def async_will_remove_from_hass(self):
        """Cleanup the entity."""
        self.clear_listener()

    @property
    def device_info(self):
        """Holds the available information about the device."""
        if self.has_attribute(AttributeType.FIRMWARE_REVISION):
            sw_version = self.attribute(AttributeType.FIRMWARE_REVISION)
        elif self.has_attribute(AttributeType.SOFTWARE_REVISION):
            sw_version = self.attribute(AttributeType.SOFTWARE_REVISION)
        else:
            sw_version = "undefined"

        return {
            "identifiers": {
                # Serial numbers are unique IDs within a specific domain
                (DOMAIN, self._node.id)
            },
            "name": self._node.name,
            "manufacturer": "unknown",
            "model": get_attribute_for_enum(
                NodeProfile, self._homee_data["profile"]
            ).lower(),
            "sw_version": sw_version,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    @property
    def available(self) -> bool:
        """Return the availablity of the underlying node."""
        return self._node.state <= 1

    @property
    def should_poll(self) -> bool:
        """Return if the entity should poll."""
        return False

    @property
    def raw_data(self):
        """Return the raw data of the node."""
        return self._node._data

    @property
    def extra_state_attributes(self) -> dict[str, dict]:
        """Return entity specific state attributes."""
        data = {}

        if self._entry.options.get(CONF_ADD_HOMEE_DATA, False):
            data[ATTR_HOMEE_DATA] = self._homee_data

        return data if data else None

    async def async_update(self):
        """Fetch new state data for this light."""
        self._node._remap_attributes()

    def register_listener(self):
        """Register the on_changed listener on the node."""
        self._clear_node_listener = self._node.add_on_changed_listener(
            self._on_node_updated
        )

    def clear_listener(self):
        """Clear the on_changed listener on the node."""
        if self._clear_node_listener is not None:
            self._clear_node_listener()

    def attribute(self, attribute_type):
        """Try to get the current value of the attribute of the given type."""
        try:
            attribute = self._node.get_attribute_by_type(attribute_type)
        except Exception:
            raise AttributeNotFoundException(attribute_type) from None

        # If the unit of the attribute is 'text', it is stored in .data
        if attribute.unit == "text":
            return self._node.get_attribute_by_type(attribute_type).data

        return self._node.get_attribute_by_type(attribute_type).current_value

    def get_attribute(self, attribute_type):
        """Get the attribute object of the given type."""
        return self._node.get_attribute_by_type(attribute_type)

    def has_attribute(self, attribute_type):
        """Check if an attribute of the given type exists."""
        return attribute_type in self._node._attribute_map

    def is_reversed(self, attribute_type) -> bool:
        """Check if movement direction is reversed."""
        attribute = self._node.get_attribute_by_type(attribute_type)
        if hasattr(attribute, "options"):
            if hasattr(attribute.options, "reverse_control_ui"):
                if attribute.options.reverse_control_ui:
                    return True

        return False

    async def async_set_value(self, attribute_type: int, value: float):
        """Set an attribute value on the homee node."""
        await self.async_set_value_by_id(self.get_attribute(attribute_type).id, value)

    async def async_set_value_by_id(self, attribute_id: int, value: float):
        """Set an attribute value on the homee node."""
        await self._entity.hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_NODE: self._node.id,
                ATTR_ATTRIBUTE: attribute_id,
                ATTR_VALUE: value,
            },
        )

    def _on_node_updated(self, node: HomeeNode, attribute: HomeeAttribute):
        self._entity.schedule_update_ha_state()


class AttributeNotFoundException(Exception):
    """Raised if a requested attribute does not exist on a homee node."""

    def __init__(self, attributeType) -> None:
        """Initialize the exception."""
        self.attributeType = attributeType


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
