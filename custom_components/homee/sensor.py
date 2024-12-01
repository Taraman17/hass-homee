"""The homee sensor platform."""

import logging

from pyHomee import Homee
from pyHomee.const import AttributeType, NodeProtocol, NodeState
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import HomeeNodeEntity, helpers
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_ATTRIBUTES = [
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.BATTERY_LEVEL,
    AttributeType.BRIGHTNESS,
    AttributeType.BUTTON_STATE,
    AttributeType.CURRENT,
    AttributeType.CURRENT_ENERGY_USE,
    AttributeType.CURRENT_VALVE_POSITION,
    AttributeType.DAWN,
    AttributeType.DEVICE_TEMPERATURE,
    AttributeType.LINK_QUALITY,
    AttributeType.POSITION,
    AttributeType.RELATIVE_HUMIDITY,
    AttributeType.TEMPERATURE,
    AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_VOLTAGE,
    AttributeType.UP_DOWN,
    AttributeType.UV,
    AttributeType.VOLTAGE,
    AttributeType.WIND_SPEED,
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
    AttributeType.CURRENT_VALVE_POSITION,
    AttributeType.DAWN,
    AttributeType.DEVICE_TEMPERATURE,
    AttributeType.LINK_QUALITY,
    AttributeType.POSITION,
    AttributeType.RAIN_FALL,
    AttributeType.RELATIVE_HUMIDITY,
    AttributeType.TEMPERATURE,
    AttributeType.TOTAL_CURRENT_ENERGY_USE,
    AttributeType.TOTAL_CURRENT,
    AttributeType.UV,
    AttributeType.VOLTAGE,
]

TOTAL_INCREASING_ATTRIBUTES = [
    AttributeType.ACCUMULATED_ENERGY_USE,
    AttributeType.RAIN_FALL_LAST_HOUR,
    AttributeType.RAIN_FALL_TODAY,
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
    entity_category = None

    if attribute.type == AttributeType.BATTERY_LEVEL:
        device_class = SensorDeviceClass.BATTERY
        translation_key = "battery_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.BRIGHTNESS:
        device_class = SensorDeviceClass.ILLUMINANCE
        translation_key = "brightness_sensor"

    if attribute.type == AttributeType.BUTTON_STATE:
        translation_key = "button_state_sensor"

    if attribute.type in [AttributeType.CURRENT, AttributeType.TOTAL_CURRENT]:
        device_class = SensorDeviceClass.CURRENT
        translation_key = "current_sensor"

    if attribute.type == AttributeType.CURRENT_VALVE_POSITION:
        translation_key = "valve_position_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.DAWN:
        translation_key = "dawn_sensor"
        device_class = SensorDeviceClass.ILLUMINANCE

    if attribute.type in [
        AttributeType.ACCUMULATED_ENERGY_USE,
        AttributeType.TOTAL_ACCUMULATED_ENERGY_USE,
    ]:
        device_class = SensorDeviceClass.ENERGY
        translation_key = "energy_sensor"

    if attribute.type == AttributeType.RELATIVE_HUMIDITY:
        device_class = SensorDeviceClass.HUMIDITY
        translation_key = "relative_humidity_sensor"

    if attribute.type == AttributeType.LINK_QUALITY:
        translation_key = "link_quality_sensor"
        icon = "mdi:signal"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.POSITION:
        translation_key = "position_sensor"

    if attribute.type in [
        AttributeType.CURRENT_ENERGY_USE,
        AttributeType.TOTAL_CURRENT_ENERGY_USE,
    ]:
        device_class = SensorDeviceClass.POWER
        translation_key = "power_sensor"

    if attribute.type == AttributeType.RAIN_FALL_LAST_HOUR:
        device_class = SensorDeviceClass.PRECIPITATION
        translation_key = "rainfall_hour_sensor"

    if attribute.type == AttributeType.RAIN_FALL_TODAY:
        device_class = SensorDeviceClass.PRECIPITATION
        translation_key = "rainfall_day_sensor"

    if attribute.type == AttributeType.TEMPERATURE:
        device_class = SensorDeviceClass.TEMPERATURE
        translation_key = "temperature_sensor"

    if attribute.type == AttributeType.DEVICE_TEMPERATURE:
        device_class = SensorDeviceClass.TEMPERATURE
        translation_key = "device_temperature_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.UP_DOWN:
        translation_key = "up_down_sensor"

    if attribute.type == AttributeType.UV:
        translation_key = "uv_sensor"

    if attribute.type in [AttributeType.VOLTAGE, AttributeType.TOTAL_VOLTAGE]:
        device_class = SensorDeviceClass.VOLTAGE
        translation_key = "voltage_sensor"

    if attribute.type == AttributeType.WIND_SPEED:
        translation_key = "wind_speed_sensor"
        device_class = SensorDeviceClass.WIND_SPEED

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

    return (device_class, translation_key, icon, entity_category)


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
        props = ["state", "protocol"]
        devices.extend(HomeeNodeSensor(node, config_entry, item) for item in props)
        devices.extend(
            HomeeSensor(node, config_entry, attribute)
            for attribute in node.attributes
            if attribute.type in SENSOR_ATTRIBUTES
        )
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
            self._translation_key,
            self._attr_icon,
            self._attr_entity_category,
        ) = get_device_properties(measurement_attribute)
        self._state_class = get_state_class(measurement_attribute)
        self._sensor_index = measurement_attribute.instance
        if self._translation_key is None:
            self._attr_name = None

        self._attr_unique_id = f"{self._node.id}-sensor-{self._measurement.id}"

    @property
    def translation_key(self) -> str:
        """Return the translation key of the sensor entity."""
        if self.is_reversed(self._measurement.type):
            return f"{self._translation_key}_rev"

        return self._translation_key

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        if self._measurement.type in TEXT_STATUS_ATTRIBUTES:
            return int(self._measurement.current_value)

        # TODO: If HA supports klx as unit, remove.
        if self._measurement.unit == "klx":
            return self._measurement.current_value * 1000

        return self._measurement.current_value

    @property
    def native_unit_of_measurement(self):
        """Return the native unit of the sensor."""
        if self._measurement.unit == "n/a":
            return None
        if self.translation_key == "uv_sensor":
            return "UV Index"

        # TODO: If HA supports klx as unit, remove.
        if self._measurement.unit == "klx":
            return "lx"

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
        entry: ConfigEntry,
        prop_name: str,
    ) -> None:
        """Initialize a homee node sensor entity."""
        self._node = node
        self._entry = entry
        self._prop_name = prop_name
        self._attr_available = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = f"node_sensor_{prop_name}"

        self._attr_unique_id = f"{node.id}-sensor-{prop_name}"

    @property
    def native_value(self) -> str:
        """Return the sensors value."""
        value = getattr(self._node, self._prop_name)
        att_class = {"state": NodeState, "protocol": NodeProtocol}

        state = helpers.get_name_for_enum(att_class[self._prop_name], value)
        return state.lower()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        homee: Homee = self.hass.data[DOMAIN][self._entry.entry_id]
        if self._node.id == -1:
            return DeviceInfo(
                identifiers={(DOMAIN, homee.device_id)},
            )

        return DeviceInfo(
            identifiers={(DOMAIN, self._node.id)},
        )

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return the default enabled state."""
        return False
