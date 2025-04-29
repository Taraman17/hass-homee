"""The homee alarm control panel platform."""

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeeConfigEntry
from .entity import HomeeNodeEntity
from .helpers import migrate_old_unique_ids

PARALLEL_UPDATES = 0


def get_features(attribute: HomeeAttribute) -> AlarmControlPanelEntityFeature:
    """Return the features of the alarm panel based on the atribute type."""
    if attribute.type == AttributeType.HOMEE_MODE:
        return (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.ARM_VACATION
        )

    return AlarmControlPanelEntityFeature(0)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomeeConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Add the homee platform for the switch component."""

    devices: list[HomeeAlarmPanel] = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeAlarmPanel(node, config_entry, attribute)
            for attribute in node.attributes
            if attribute.type == AttributeType.HOMEE_MODE
            and attribute.editable
            and node.id == -1
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.ALARM_CONTROL_PANEL)
        async_add_devices(devices)


class HomeeAlarmPanel(HomeeNodeEntity, AlarmControlPanelEntity):
    """Representation of a homee alarm control panel."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: HomeeConfigEntry,
        alarm_panel_attribute: HomeeAttribute,
    ) -> None:
        """Initialize a homee alarm Control panel entity."""
        HomeeNodeEntity.__init__(self, node, entry)
        self._attr_code_arm_required = False
        self._alarm_panel_attribute = alarm_panel_attribute
        self._attr_supported_features = get_features(alarm_panel_attribute)
        self._attr_translation_key = "homee_status"

        self._attr_unique_id = f"{entry.runtime_data.settings.uid}-{node.id}-{self._alarm_panel_attribute.id}"

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the alarm-panel entity."""
        return f"{self._node.id}-alarm_panel-{self._alarm_panel_attribute.id}"

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return current state."""
        curr_state = int(self._alarm_panel_attribute.current_value)
        return {
            0: AlarmControlPanelState.ARMED_HOME,
            1: AlarmControlPanelState.ARMED_NIGHT,
            2: AlarmControlPanelState.ARMED_AWAY,
            3: AlarmControlPanelState.ARMED_VACATION,
        }.get(curr_state)

    async def async_update(self) -> None:
        """Update entity from homee."""
        homee = self._entry.runtime_data
        await homee.update_attribute(
            self._alarm_panel_attribute.node_id, self._alarm_panel_attribute.id
        )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        # Homee does not offer a disarm command. However, we cannot get
        # rid of this function, so we ignore.

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.async_set_value(self._alarm_panel_attribute, 0)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        await self.async_set_value(self._alarm_panel_attribute, 1)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.async_set_value(self._alarm_panel_attribute, 2)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        await self.async_set_value(self._alarm_panel_attribute, 3)
