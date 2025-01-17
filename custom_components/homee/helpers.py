"""Helper functions for the homee custom component."""

import logging

from pyHomee import Homee
from pyHomee.model import HomeeNode

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .entity import HomeeNodeEntity

_LOGGER = logging.getLogger(__name__)


def get_imported_nodes(config_entry) -> list[HomeeNode]:
    """Get a list of nodes that should be imported."""
    homee: Homee = config_entry.runtime_data
    return homee.nodes


def get_name_for_enum(att_class, att_id) -> str:
    """Return the enum item name for a given integer."""
    try:
        attribute_name = att_class(att_id).name
    except ValueError:
        _LOGGER.warning("Value %s does not exist in %s", att_id, att_class.__name__)
        return "Unknown"

    return attribute_name


async def migrate_old_unique_ids(
    hass: HomeAssistant, devices: list[HomeeNodeEntity], platform: str
) -> None:
    """Migrate uids for upcoming HA core integration."""
    registry = er.async_get(hass)
    for device in devices:
        old_entity_id = registry.async_get_entity_id(
            platform, DOMAIN, device.old_unique_id
        )
        updated_unique_id = device.unique_id
        if old_entity_id is not None and updated_unique_id is not None:
            _LOGGER.debug(
                "Migrating unique_id from [%s] to [%s]",
                device.old_unique_id,
                device.unique_id,
            )
            registry.async_update_entity(old_entity_id, new_unique_id=updated_unique_id)
