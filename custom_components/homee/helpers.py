"""Helper functions for the homee custom component."""

import logging

from pyHomee import Homee
from pyHomee.model import HomeeNode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_imported_nodes(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> list[HomeeNode]:
    """Get a list of nodes that should be imported."""
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]
    return homee.nodes

def get_name_for_enum(att_class, att_id):
    """Return the enum item name for a given integer."""
    try:
        attribute_name = att_class(att_id).name
    except ValueError:
        _LOGGER.warning("Value %s does not exist in %s", att_id, att_class.__name__)
        return "Unknown"

    return attribute_name
