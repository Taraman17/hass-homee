"""The homee lock platform."""

import logging

from pyHomee.const import AttributeChangedBy, AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.lock import LockEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import HomeeConfigEntry
from .entity import HomeeNodeEntity
from .helpers import get_name_for_enum, migrate_old_unique_ids

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
):
    """Add the homee platform for the lock component."""

    devices = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeLock(node, config_entry, attribute)
            for attribute in node.attributes
            if (attribute.type == AttributeType.LOCK_STATE and attribute.editable)
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.LOCK)
        async_add_devices(devices)


class HomeeLock(HomeeNodeEntity, LockEntity):
    """Representation of a homee lock."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        node: HomeeNode,
        entry: HomeeConfigEntry,
        lock_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee switch entity."""
        HomeeNodeEntity.__init__(self, node, entry)
        self._lock = lock_attribute
        self._switch_index = lock_attribute.instance
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._node.id}-{self._lock.id}"
        )

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._node.id}-lock-{self._lock.id}"

    @property
    def is_locked(self) -> int:
        """Return the current lock state."""
        return self._lock.current_value

    @property
    def changed_by(self) -> str:
        """Return by what the lock was last changed."""
        changed_by_name = get_name_for_enum(AttributeChangedBy, self._lock.changed_by)
        return f"{changed_by_name}-{self._lock.changed_by_id}"

    async def async_update(self) -> None:
        """Update entity from homee."""
        homee = self._entry.runtime_data
        await homee.update_attribute(self._lock.node_id, self._lock.id)

    async def async_lock(self, **kwargs) -> None:
        """Lock all or specified locks. A code to lock the lock with may be specified."""
        await self.async_set_value(self._lock, 0)

    async def async_unlock(self, **kwargs) -> None:
        """Unlock all or specified locks. A code to unlock the lock with may be specified."""
        await self.async_set_value(self._lock, 1)
