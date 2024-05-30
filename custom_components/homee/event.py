"""The homee event platform."""

import logging

from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from . import HomeeNodeEntity
from .helpers import get_imported_nodes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the event component."""

    devices = []
    for node in get_imported_nodes(hass, config_entry):
        devices.extend(
            HomeeEvent(node, config_entry, attribute)
            for attribute in node.attributes
            if (attribute.type == AttributeType.UP_DOWN_REMOTE)
        )
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeEvent(HomeeNodeEntity, EventEntity):
    """Representation of a homee event."""

    entity_description = EventEntityDescription(
        key="up_down_remote",
        device_class=EventDeviceClass.BUTTON,
        event_types=["0", "1", "2", "3", "4", "5", "6", "7", "9"],
        translation_key="up_down_remote",
        has_entity_name=True,
    )

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        event_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee event entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._event = event_attribute
        self._switch_index = event_attribute.instance
        self._attr_unique_id = f"{self._node.id}-event-{self._event.id}"

    @callback
    def _async_handle_event(self, event: HomeeAttribute) -> None:
        """Handle a homee event."""
        self._trigger_event(int(event.current_value))
        self.async_write_ha_state()
