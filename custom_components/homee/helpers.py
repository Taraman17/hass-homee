"""Helper functions for the homee custom component."""
import inspect

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pymee import Homee
from pymee.model import HomeeNode

from .const import CONF_ALL_DEVICES, CONF_GROUPS, CONF_IMPORT_GROUPS, DOMAIN


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


def get_attribute_for_enum(att_class, att_id):
    """Return the attribute label for a given integer."""
    attributes = [
        a
        for a in inspect.getmembers(att_class, lambda a: not inspect.isroutine(a))
        if not (a[0].startswith("__") and a[0].endswith("__"))
    ]
    attribute_label = [a[0] for a in attributes if a[1] == att_id]
    if not attribute_label:
        return None
    return attribute_label[0]
