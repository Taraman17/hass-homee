"""The homee lock platform."""

import logging

from pymee.const import AttributeChangedBy, AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import HomeeNodeEntity
from .helpers import get_attribute_for_enum, get_imported_nodes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the lock component."""

    devices = []
    for node in get_imported_nodes(hass, config_entry):
        devices.extend(
            HomeeLock(node, config_entry, attribute)
            for attribute in node.attributes
            if (attribute.type == AttributeType.LOCK_STATE and attribute.editable)
        )
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeLock(HomeeNodeEntity, LockEntity):
    """Representation of a homee lock."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        lock_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee switch entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._lock = lock_attribute
        self._switch_index = lock_attribute.instance
        self._attr_unique_id = f"{self._node.id}-lock-{self._lock.id}"

    @property
    def is_locked(self) -> int:
        """Return the current lock state."""
        return self._lock.current_value

    @property
    def changed_by(self) -> str:
        """Return by what the lock was last changed."""
        return f"{get_attribute_for_enum(AttributeChangedBy, self._lock.changed_by)}-{self._lock.changed_by_id}"

    async def async_lock(self, **kwargs):
        """Lock all or specified locks. A code to lock the lock with may optionally be specified."""
        await self.async_set_value_by_id(self._lock.id, 0)

    async def async_unlock(self, **kwargs):
        """Unlock all or specified locks. A code to unlock the lock with may optionally be specified."""
        await self.async_set_value_by_id(self._lock.id, 1)
