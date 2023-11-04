"""The homee switch platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

HOMEE_PLUG_PROFILES = [
    NodeProfile.ON_OFF_PLUG,
    NodeProfile.METERING_PLUG,
    NodeProfile.DOUBLE_ON_OFF_PLUG,
    NodeProfile.IMPULSE_PLUG,
]

HOMEE_SWITCH_ATTRIBUTES = [
    AttributeType.AUTOMATIC_MODE_IMPULSE,
    AttributeType.BRIEFLY_OPEN_IMPULSE,
    AttributeType.IMPULSE,
    AttributeType.LIGHT_IMPULSE,
    AttributeType.OPEN_PARTIAL_IMPULSE,
    AttributeType.ON_OFF,
    AttributeType.PERMANENTLY_OPEN_IMPULSE,
    AttributeType.RESET_METER,
    AttributeType.SIREN,
    AttributeType.SLAT_ROTATION_IMPULSE,
    AttributeType.VENTILATE_IMPULSE,
    AttributeType.WATCHDOG_ON_OFF,
]

DESCRIPTIVE_ATTRIBUTES = [
    AttributeType.AUTOMATIC_MODE_IMPULSE,
    AttributeType.BRIEFLY_OPEN_IMPULSE,
    AttributeType.LIGHT_IMPULSE,
    AttributeType.OPEN_PARTIAL_IMPULSE,
    AttributeType.PERMANENTLY_OPEN_IMPULSE,
    AttributeType.RESET_METER,
    AttributeType.SLAT_ROTATION_IMPULSE,
    AttributeType.VENTILATE_IMPULSE,
    AttributeType.WATCHDOG_ON_OFF,
]


def get_device_class(node: HomeeNode) -> int:
    """Determine the device class a homee node based on the node profile."""
    if node.profile in HOMEE_PLUG_PROFILES:
        return SwitchDeviceClass.OUTLET

    return SwitchDeviceClass.SWITCH


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the switch component."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        for attribute in node.attributes:
            # These conditions identify a switch.
            if attribute.type in HOMEE_SWITCH_ATTRIBUTES and attribute.editable:
                devices.append(HomeeSwitch(node, config_entry, attribute))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeSwitch(HomeeNodeEntity, SwitchEntity):
    """Representation of a homee switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        on_off_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee switch entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._on_off = on_off_attribute
        self._switch_index = on_off_attribute.instance
        self._device_class = get_device_class(node)

        self._unique_id = f"{self._node.id}-switch-{self._on_off.id}"

    @property
    def translation_key(self) -> str | None:
        """Return the translation key for the switch."""
        # If a switch is the main feature of a device it will get its name.
        translation_key = None

        attribute_name = helpers.get_attribute_name(self._on_off.type)

        # If a switch type has more than one instance,
        # it will be named and numbered.
        if self._on_off.instance > 0:
            translation_key = f"{attribute_name.lower()}_" f"{self._on_off.instance}"
        # Some switches should always be named descriptive.
        elif self._on_off.type in DESCRIPTIVE_ATTRIBUTES:
            translation_key = attribute_name.lower()

        if self._on_off.instance > 4:
            _LOGGER.error(
                "Did get more than 4 switches of a type,"
                "please report at"
                "https://github.com/Taraman17/hacs-homee/issues"
            )

        if translation_key is None:
            self._attr_name = None

        return translation_key

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return bool(self._on_off.current_value)

    @property
    def icon(self) -> str | None:
        """Return icon if different from main feature."""
        if self._on_off.type == AttributeType.WATCHDOG_ON_OFF:
            return "mdi:dog"

        return None

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.async_set_value_by_id(self._on_off.id, 1)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.async_set_value_by_id(self._on_off.id, 0)

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        if self.has_attribute(AttributeType.CURRENT_ENERGY_USE):
            return self.attribute(AttributeType.CURRENT_ENERGY_USE)
        else:
            return None

    @property
    def today_energy_kwh(self):
        """Return the total power usage in kWh."""
        if self.has_attribute(AttributeType.ACCUMULATED_ENERGY_USE):
            return self.attribute(AttributeType.ACCUMULATED_ENERGY_USE)
        else:
            return None

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class
