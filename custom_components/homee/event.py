"""The homee event platform."""

import logging

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from . import HomeeConfigEntry
from .entity import HomeeNodeEntity
from .helpers import get_imported_nodes, migrate_old_unique_ids

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
) -> None:
    """Add the homee platform for the event component."""

    devices = []
    for node in get_imported_nodes(config_entry):
        devices.extend(
            HomeeEvent(node, config_entry, attribute)
            for attribute in node.attributes
            if (attribute.type == AttributeType.UP_DOWN_REMOTE)
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.EVENT)
        async_add_devices(devices)


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
        entry: HomeeConfigEntry,
        event_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee event entity."""
        HomeeNodeEntity.__init__(self, node, entry)
        self._event = event_attribute
        self._switch_index = event_attribute.instance
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._node.id}-{self._event.id}"
        )

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._node.id}-event-{self._event.id}"

    @callback
    def _async_handle_event(self, node: HomeeNode) -> None:
        """Handle a homee event."""
        event = node.get_attribute_by_type(AttributeType.UP_DOWN_REMOTE)
        if event.type == AttributeType.UP_DOWN_REMOTE:
            self._trigger_event(str(int(event.current_value)))
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callback for HomeeEvent."""
        self._node.add_on_changed_listener(self._async_handle_event)
