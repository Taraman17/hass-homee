"""The homee alarm control panel platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry

from pymee import Homee
from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_features(attribute) -> int:
    """Return the features of the alarm panel based on the atribute type."""
    if attribute.type == AttributeType.HOMEE_MODE:
        return (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.ARM_VACATION
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_devices
):
    """Add the homee platform for the switch component."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        for attribute in node.attributes:
            # These conditions identify a switch.
            if attribute.type == AttributeType.HOMEE_MODE and\
               attribute.editable:
                devices.append(HomeeAlarmPanel(node, config_entry, attribute))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeAlarmPanel(HomeeNodeEntity, AlarmControlPanelEntity):
    """Representation of a homee alarm control panel."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        alarm_panel_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee alarm Control panel entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._attr_code_arm_required = False
        self._alarm_panel_attribute = alarm_panel_attribute
        self._attr_supported_features = get_features(alarm_panel_attribute)
        self._attr_translation_key = "homee_status"

        self._unique_id = (
            f"{self._node.id}-alarm_panel-" f"{self._alarm_panel_attribute.id}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        homee: Homee = self.hass.data[DOMAIN][self._entry.entry_id]
        return DeviceInfo(
            identifiers={(DOMAIN, homee.deviceId)},
            name=homee.settings.homee_name,
            manufacturer="homee",
            model="homee",
            sw_version=homee.settings.version,
            hw_version="TBD",
        )

    @property
    def state(self) -> int:
        """Return current state."""
        return int(self._alarm_panel_attribute.current_value)

    async def async_alarm_disarm(self, code=None) -> None:
        """Send disarm command."""
        # Homee does not offer a disarm command. However, we cannot get
        # rid of this function, so we ignore.

    async def async_alarm_arm_home(self, code=None) -> None:
        """Send arm home command."""
        await self.async_set_value_by_id(self._alarm_panel_attribute.id, 0)

    async def async_alarm_arm_away(self, code=None) -> None:
        """Send arm away command."""
        await self.async_set_value_by_id(self._alarm_panel_attribute.id, 2)

    async def async_alarm_arm_night(self, code=None) -> None:
        """Send arm night command."""
        await self.async_set_value_by_id(self._alarm_panel_attribute.id, 1)

    async def async_alarm_arm_vacation(self, code=None) -> None:
        """Send arm vacation command."""
        await self.async_set_value_by_id(self._alarm_panel_attribute.id, 3)
