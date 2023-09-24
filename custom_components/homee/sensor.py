"""The homee sensor platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

SENSOR_ATTRIBUTES = [
    AttributeType.CURRENT_ENERGY_USE,
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.POSITION,
    AttributeType.UP_DOWN,
    AttributeType.BATTERY_LEVEL,
    AttributeType.CURRENT,
    AttributeType.VOLTAGE,
    AttributeType.TOTAL_VOLTAGE,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.DEVICE_TEMPERATURE,
]

MEASUREMENT_ATTRIBUTES = [
    AttributeType.CURRENT_ENERGY_USE,
    AttributeType.POSITION,
    AttributeType.UP_DOWN,
    AttributeType.BATTERY_LEVEL,
    AttributeType.CURRENT,
    AttributeType.VOLTAGE,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.DEVICE_TEMPERATURE,
]

TOTAL_INCREASING_ATTRIBUTES = [
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
]


def get_device_class(attribute: HomeeAttribute) -> int:
    """Determine the device class a homee node based on the node profile."""
    device_class = None

    if attribute.type == AttributeType.CURRENT_ENERGY_USE:
        device_class = SensorDeviceClass.POWER

    if attribute.type in [AttributeType.ACCUMULATED_ENERGY_USE, AttributeType.TOTAL_ACCUMULATED_ENERGY_USE]:
        device_class = SensorDeviceClass.ENERGY

    if attribute.type == AttributeType.BATTERY_LEVEL:
        device_class = SensorDeviceClass.BATTERY

    if attribute.type in [AttributeType.VOLTAGE, AttributeType.TOTAL_VOLTAGE]:
        device_class = SensorDeviceClass.VOLTAGE

    if attribute.type in [AttributeType.CURRENT, AttributeType.TOTAL_CURRENT]:
        device_class = SensorDeviceClass.CURRENT

    if attribute.type in [AttributeType.DEVICE_TEMPERATURE, AttributeType.TEMPERATURE]:
        device_class = SensorDeviceClass.TEMPERATURE

    if attribute.type in [AttributeType.CURRENT_ENERGY_USE, AttributeType.TOTAL_CURRENT_ENERGY_USE]:
        device_class = SensorDeviceClass.POWER

    return device_class


def get_state_class(attribute: HomeeAttribute) -> int:
    """Determine the device class a homee node based on the node profile."""
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
    _attr_name = None

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        measurement_attribute: HomeeAttribute = None
    ) -> None:
        """Initialize a homee sensor entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._measurement = measurement_attribute
        self._device_class = get_device_class(measurement_attribute)
        self._state_class = get_state_class(measurement_attribute)
        self._sensor_index = measurement_attribute.instance

        self._unique_id = f"{self._node.id}-sensor-{self._measurement.id}"

    @property
    def name(self):
        """Return the display name of this entity."""
        if self._measurement.name not in ["", "None"]:
            name = f"{self._measurement.name}"
        elif self._device_class:
            name = f"{self._device_class}"
        else:
            for key, val in AttributeType.__dict__.items():
                if val == self._measurement.type:
                    name = f"{key}"

        if self._sensor_index > 0:
            name = f"{name} {self._sensor_index}"

        return name

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self._measurement.current_value

    @property
    def native_unit_of_measurement(self):
        """Return the native unit of the sensor."""
        return self._measurement.unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return self._state_class

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class
