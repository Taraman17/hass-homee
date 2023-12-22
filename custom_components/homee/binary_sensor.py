"""The homee binary sensor platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers
from .const import CONF_DOOR_GROUPS, CONF_GROUPS, CONF_WINDOW_GROUPS

_LOGGER = logging.getLogger(__name__)

HOMEE_BINARY_SENSOR_ATTRIBUTES = [
    AttributeType.BATTERY_LOW_ALARM,
    AttributeType.HIGH_TEMPERATURE_ALARM,
    AttributeType.FLOOD_ALARM,
    AttributeType.LOCK_STATE,
    AttributeType.ON_OFF,
    AttributeType.OPEN_CLOSE,
    AttributeType.SMOKE_ALARM,
    AttributeType.PRESENCE_ALARM,
]


def get_device_class(attribute: HomeeAttribute) -> int:
    """Determine the device class a homee node based on the available attributes."""
    device_class = BinarySensorDeviceClass.OPENING
    state_attr = AttributeType.OPEN_CLOSE
    translation_key = "opening_sensor"

    if attribute.type == AttributeType.BATTERY_LOW_ALARM:
        state_attr = AttributeType.BATTERY_LOW_ALARM
        device_class = BinarySensorDeviceClass.BATTERY
        translation_key = "battery_low_sensor"

    if attribute.type == AttributeType.HIGH_TEMPERATURE_ALARM:
        state_attr = AttributeType.HIGH_TEMPERATURE_ALARM
        device_class = BinarySensorDeviceClass.HEAT
        translation_key = "heat_sensor"

    if attribute.type == AttributeType.FLOOD_ALARM:
        state_attr = AttributeType.FLOOD_ALARM
        device_class = BinarySensorDeviceClass.MOISTURE
        translation_key = "flood_sensor"

    if attribute.type == AttributeType.ON_OFF:
        state_attr = AttributeType.ON_OFF
        device_class = BinarySensorDeviceClass.PLUG
        translation_key = "plug_sensor"

    if attribute.type == AttributeType.LOCK_STATE:
        state_attr = AttributeType.LOCK_STATE
        device_class = BinarySensorDeviceClass.LOCK
        translation_key = "lock_sensor"

    if attribute.type == AttributeType.SMOKE_ALARM:
        state_attr = AttributeType.SMOKE_ALARM
        device_class = BinarySensorDeviceClass.SMOKE
        translation_key = "smoke_sensor"

    if attribute.type == AttributeType.PRESENCE_ALARM:
        state_attr = AttributeType.PRESENCE_ALARM
        device_class = BinarySensorDeviceClass.MOTION
        translation_key = "motion_sensor"

    return (device_class, state_attr, translation_key)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the binary sensor integration."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        for attribute in node.attributes:
            # Determine if the entity is a binary sensor.
            if (
                attribute.type in HOMEE_BINARY_SENSOR_ATTRIBUTES
                and not attribute.editable
            ):
                devices.append(HomeeBinarySensor(node, config_entry, attribute))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeBinarySensor(HomeeNodeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        binary_sensor_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee binary sensor entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)

        self._on_off = binary_sensor_attribute
        self._configure_device_class()
        self._attr_unique_id = f"{self._node.id}-binary_sensor-{self._on_off.id}"

    def _configure_device_class(self):
        """Configure the device class of the sensor."""

        # Get the initial device class and state attribute
        (
            self._device_class,
            self._state_attr,
            self._attr_translation_key,
        ) = get_device_class(self._on_off)

        # Set Window/Door device class based on configured groups
        if any(
            str(group.id)
            in self._entry.options[CONF_GROUPS].get(CONF_WINDOW_GROUPS, [])
            for group in self._node.groups
        ):
            self._device_class = BinarySensorDeviceClass.WINDOW
            self._attr_translation_key = "window_sensor"
        elif any(
            str(group.id) in self._entry.options[CONF_GROUPS].get(CONF_DOOR_GROUPS, [])
            for group in self._node.groups
        ):
            self._device_class = BinarySensorDeviceClass.DOOR
            self._attr_translation_key = "door_sensor"

        if self.translation_key is None:
            self._attr_name = None

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self.attribute(self._state_attr))

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class
