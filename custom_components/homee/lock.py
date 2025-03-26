"""The homee lock platform."""

from typing import Any

from pyHomee.const import AttributeChangedBy, AttributeType

from homeassistant.components.lock import LockEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeeConfigEntry
from .entity import HomeeEntity
from .helpers import get_name_for_enum, migrate_old_unique_ids

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Add the homee platform for the lock component."""

    devices: list[HomeeLock] = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeLock(attribute, config_entry)
            for attribute in node.attributes
            if (attribute.type == AttributeType.LOCK_STATE and attribute.editable)
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.LOCK)
        async_add_devices(devices)


class HomeeLock(HomeeEntity, LockEntity):
    """Representation of a homee lock."""

    _attr_name = None

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the lock entity."""
        return f"{self._attribute.node_id}-lock-{self._attribute.id}"

    @property
    def is_locked(self) -> bool:
        """Return the current lock state."""
        return self._attribute.current_value == 1.0

    @property
    def is_locking(self) -> bool:
        """Return if lock is locking."""
        return self._attribute.target_value > self._attribute.current_value

    @property
    def is_unlocking(self) -> bool:
        """Return if lock is unlocking."""
        return self._attribute.target_value < self._attribute.current_value

    @property
    def changed_by(self) -> str:
        """Return by whom or what the lock was last changed."""
        changed_id = str(self._attribute.changed_by_id)
        changed_by_name = get_name_for_enum(
            AttributeChangedBy, self._attribute.changed_by
        )
        if self._attribute.changed_by == AttributeChangedBy.USER:
            changed_id = self._entry.runtime_data.get_user_by_id(
                self._attribute.changed_by_id
            ).username

        return f"{changed_by_name}-{changed_id}"

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock all or specified locks. A code to lock the lock with may be specified."""
        await self.async_set_value(1)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock all or specified locks. A code to unlock the lock with may be specified."""
        await self.async_set_value(0)
