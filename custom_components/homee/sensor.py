"""The homee sensor platform."""

import logging

from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

SENSOR_ATTRIBUTES = [
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.BATTERY_LEVEL,
    AttributeType.BRIGHTNESS,
    AttributeType.BUTTON_STATE,
    AttributeType.CURRENT,
    AttributeType.CURRENT_ENERGY_USE,
    AttributeType.DEVICE_TEMPERATURE,
    AttributeType.LINK_QUALITY,
    AttributeType.POSITION,
    AttributeType.TEMPERATURE,
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_VOLTAGE,
    AttributeType.UP_DOWN,
    AttributeType.VOLTAGE,
    AttributeType.WINDOW_POSITION,
]

TOTAL_VALUES = [
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_VOLTAGE,
]

MEASUREMENT_ATTRIBUTES = [
    AttributeType.BATTERY_LEVEL,
    AttributeType.BRIGHTNESS,
    AttributeType.BUTTON_STATE,
    AttributeType.CURRENT,
    AttributeType.CURRENT_ENERGY_USE,
    AttributeType.DEVICE_TEMPERATURE,
    AttributeType.LINK_QUALITY,
    AttributeType.POSITION,
    AttributeType.TEMPERATURE,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.VOLTAGE,
]

TOTAL_INCREASING_ATTRIBUTES = [
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
]

TEXT_STATUS_ATTRIBUTES = [
    AttributeType.UP_DOWN,
    AttributeType.WINDOW_POSITION,
]


def get_device_properties(attribute: HomeeAttribute):
    """Determine the device class of a homee entity based on it's attribute type."""
    device_class = None
    translation_key = None
    icon = None

    if attribute.type in [
        AttributeType.ACCUMULATED_ENERGY_USE,
        AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    ]:
        device_class = SensorDeviceClass.ENERGY
        translation_key = "energy_sensor"

    if attribute.type == AttributeType.BATTERY_LEVEL:
        device_class = SensorDeviceClass.BATTERY
        translation_key = "battery_sensor"

    if attribute.type == AttributeType.BRIGHTNESS:
        device_class = SensorDeviceClass.ILLUMINANCE
        translation_key = "brightness_sensor"

    if attribute.type == AttributeType.BUTTON_STATE:
        translation_key = "button_state_sensor"

    if attribute.type in [AttributeType.VOLTAGE, AttributeType.TOTAL_VOLTAGE]:
        device_class = SensorDeviceClass.VOLTAGE
        translation_key = "voltage_sensor"

    if attribute.type in [AttributeType.CURRENT, AttributeType.TOTAL_CURRENT]:
        device_class = SensorDeviceClass.CURRENT
        translation_key = "current_sensor"

    if attribute.type in [AttributeType.DEVICE_TEMPERATURE, AttributeType.TEMPERATURE]:
        device_class = SensorDeviceClass.TEMPERATURE
        translation_key = "temperature_sensor"

    if attribute.type in [
        AttributeType.CURRENT_ENERGY_USE,
        AttributeType.TOTAL_CURRENT_ENERGY_USE,
    ]:
        device_class = SensorDeviceClass.POWER
        translation_key = "power_sensor"

    if attribute.type == AttributeType.UP_DOWN:
        translation_key = "up_down_sensor"

    if attribute.type == AttributeType.POSITION:
        translation_key = "position_sensor"

    if attribute.type == AttributeType.LINK_QUALITY:
        translation_key = "link_quality_sensor"
        icon = "mdi:signal"

    if attribute.type == AttributeType.WINDOW_POSITION:
        translation_key = "window_position_sensor"
        icon = "mdi:window-closed"

    if attribute.type in TOTAL_VALUES:
        translation_key = f"total_{translation_key}"

    if attribute.instance > 0:
        translation_key = f"{translation_key}_{attribute.instance}"
        if attribute.instance > 4:
            _LOGGER.error(
                "Did get more than 4 sensors of a type,"
                "please report at https://github.com/Taraman17/hacs-homee/issues"
            )

    return (device_class, translation_key, icon)


def get_state_class(attribute: HomeeAttribute) -> int:
    """Determine the state class of a homee entity based on it's attribute type."""
    if attribute.type in MEASUREMENT_ATTRIBUTES:
        return SensorStateClass.MEASUREMENT

    if attribute.type in TOTAL_INCREASING_ATTRIBUTES:
        return SensorStateClass.TOTAL_INCREASING

    return None


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the sensor components."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        for attribute in node.attributes:
            if attribute.type in SENSOR_ATTRIBUTES:
                devices.append(HomeeSensor(node, config_entry, attribute))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeSensor(HomeeNodeEntity, SensorEntity):
    """Representation of a homee sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        measurement_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee sensor entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._measurement = measurement_attribute
        (
            self._device_class,
            self._attr_translation_key,
            self._attr_icon
        ) = get_device_properties(measurement_attribute)
        self._state_class = get_state_class(measurement_attribute)
        self._sensor_index = measurement_attribute.instance
        if self.translation_key is None:
            self._attr_name = None

        self._unique_id = f"{self._node.id}-sensor-{self._measurement.id}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        if self._measurement.type in TEXT_STATUS_ATTRIBUTES:
            return int(self._measurement.current_value)

        return self._measurement.current_value

    @property
    def native_unit_of_measurement(self):
        """Return the native unit of the sensor."""
        if self._measurement.unit == "n/a":
            return None

        return self._measurement.unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return self._state_class

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class

class HomeeNodeSensor(SensorEntity):
    """Represents a sensor based on a node's property."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        prop_name: str,
    ) -> None:
        """Initialize a homee node sensor entity."""
        self._attr_translation_key = f"node_sensor_{prop_name}"

        self.unique_id = f"{node.id}-sensor-{prop_name}"

    def get_properties(self, prop_name):
        """Get the properties for the sensor."""
        device_class = None
        state_class = None
        options = None

        if prop_name == 'state':
            device_class = SensorDeviceClass.ENUM

        return (device_class, state_class, options)