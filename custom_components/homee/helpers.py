"""Helper functions for the homee custom component."""

import inspect
import logging

from pymee import Homee
from pymee.model import HomeeNode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ALL_DEVICES, CONF_GROUPS, CONF_IMPORT_GROUPS, DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_imported_nodes(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> list[HomeeNode]:
    """Get a list of nodes that should be imported."""
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options[CONF_ALL_DEVICES]:
        return homee.nodes

    all_groups = [str(g.id) for g in homee.groups]

    # Resolve the configured group ids to actual groups
    groups = [
        homee.get_group_by_id(int(g))
        for g in config_entry.options[CONF_GROUPS].get(CONF_IMPORT_GROUPS, all_groups)
    ]

    # Add all nodes from the groups in a list
    # Make sure each node is only added once
    nodes: list[HomeeNode] = []
    for group in groups:
        for node in group.nodes:
            if node not in nodes:
                nodes.append(node)

    # Always add homee itself to the nodes.
    nodes.append(homee.get_node_by_id(-1))

    return nodes


def get_name_for_enum(att_class, att_id):
    """Return the enum item name for a given integer."""
    try:
        attribute_name = att_class(att_id).name
    except ValueError as e:
        _LOGGER.warning("Value %s does not exist in %s", att_id, att_class.__name__)
        return "Unknown"

    return attribute_name

