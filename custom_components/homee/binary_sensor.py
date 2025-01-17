"""The homee binary sensor platform."""

import logging

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant

from . import HomeeConfigEntry, helpers
from .entity import HomeeNodeEntity
from .helpers import migrate_old_unique_ids

_LOGGER = logging.getLogger(__name__)

HOMEE_BINARY_SENSOR_ATTRIBUTES = [
    AttributeType.BATTERY_LOW_ALARM,
    AttributeType.FLOOD_ALARM,
    AttributeType.HIGH_TEMPERATURE_ALARM,
    AttributeType.LOAD_ALARM,
    AttributeType.LOCK_STATE,
    AttributeType.MALFUNCTION_ALARM,
    AttributeType.MOTION_ALARM,
    AttributeType.ON_OFF,
    AttributeType.OPEN_CLOSE,
    AttributeType.OVER_CURRENT_ALARM,
    AttributeType.OVERLOAD_ALARM,
    AttributeType.PRESENCE_ALARM,
    AttributeType.RAIN_FALL,
    AttributeType.SMOKE_ALARM,
    AttributeType.SURGE_ALARM,
    AttributeType.TAMPER_ALARM,
    AttributeType.VOLTAGE_DROP_ALARM,
]


def get_device_class(attribute: HomeeAttribute):
    """Determine the device class a homee node based on the available attributes."""
    state_attr = None
    device_class = None
    translation_key = ""
    entity_category = None

    if attribute.type == AttributeType.BATTERY_LOW_ALARM:
        state_attr = AttributeType.BATTERY_LOW_ALARM
        device_class = BinarySensorDeviceClass.BATTERY
        translation_key = "battery_low_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.FLOOD_ALARM:
        state_attr = AttributeType.FLOOD_ALARM
        device_class = BinarySensorDeviceClass.MOISTURE
        translation_key = "flood_sensor"

    if attribute.type == AttributeType.HIGH_TEMPERATURE_ALARM:
        state_attr = AttributeType.HIGH_TEMPERATURE_ALARM
        device_class = BinarySensorDeviceClass.HEAT
        translation_key = "heat_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.LOAD_ALARM:
        state_attr = AttributeType.LOAD_ALARM
        translation_key = "load_alarm_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.LOCK_STATE:
        state_attr = AttributeType.LOCK_STATE
        device_class = BinarySensorDeviceClass.LOCK
        translation_key = "lock_sensor"

    if attribute.type == AttributeType.MALFUNCTION_ALARM:
        state_attr = AttributeType.MALFUNCTION_ALARM
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "malfunction_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.MOTION_ALARM:
        state_attr = AttributeType.MOTION_ALARM
        device_class = BinarySensorDeviceClass.MOTION
        translation_key = "motion_sensor"

    if attribute.type == AttributeType.ON_OFF:
        state_attr = AttributeType.ON_OFF
        device_class = BinarySensorDeviceClass.PLUG
        translation_key = "plug_sensor"

    if attribute.type == AttributeType.OPEN_CLOSE:
        state_attr = AttributeType.OPEN_CLOSE
        device_class = BinarySensorDeviceClass.OPENING
        translation_key = "opening_sensor"

    if attribute.type == AttributeType.OVER_CURRENT_ALARM:
        state_attr = AttributeType.OVER_CURRENT_ALARM
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "overcurrent_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.OVERLOAD_ALARM:
        state_attr = AttributeType.OVERLOAD_ALARM
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "overload_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.PRESENCE_ALARM:
        state_attr = AttributeType.PRESENCE_ALARM
        device_class = BinarySensorDeviceClass.MOTION
        translation_key = "motion_sensor"

    if attribute.type == AttributeType.RAIN_FALL:
        state_attr = AttributeType.RAIN_FALL
        device_class = BinarySensorDeviceClass.MOISTURE
        translation_key = "rain_sensor"

    if attribute.type == AttributeType.SMOKE_ALARM:
        state_attr = AttributeType.SMOKE_ALARM
        device_class = BinarySensorDeviceClass.SMOKE
        translation_key = "smoke_sensor"

    if attribute.type == AttributeType.SURGE_ALARM:
        state_attr = AttributeType.SURGE_ALARM
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "surge_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.TAMPER_ALARM:
        state_attr = AttributeType.TAMPER_ALARM
        device_class = BinarySensorDeviceClass.TAMPER
        translation_key = "tamper_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.VOLTAGE_DROP_ALARM:
        state_attr = AttributeType.VOLTAGE_DROP_ALARM
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "voltage_drop_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    return (device_class, state_attr, translation_key, entity_category)


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_devices
) -> None:
    """Add the homee platform for the binary sensor integration."""

    devices = []
    for node in helpers.get_imported_nodes(config_entry):
        devices.extend(
            HomeeBinarySensor(node, config_entry, attribute)
            for attribute in node.attributes
            if (
                attribute.type in HOMEE_BINARY_SENSOR_ATTRIBUTES
                and not attribute.editable
            )
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.BINARY_SENSOR)
        async_add_devices(devices)


class HomeeBinarySensor(HomeeNodeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: HomeeConfigEntry,
        binary_sensor_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee binary sensor entity."""
        HomeeNodeEntity.__init__(self, node, entry)

        self._on_off = binary_sensor_attribute
        self._configure_device_class()
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{node.id}-{self._on_off.id}"
        )

    def _configure_device_class(self):
        """Configure the device class of the sensor."""

        # Get the initial device class and state attribute
        (
            self._device_class,
            self._state_attr,
            self._attr_translation_key,
            self._attr_entity_category,
        ) = get_device_class(self._on_off)

        if self.translation_key is None:
            self._attr_name = None

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._node.id}-binary_sensor-{self._on_off.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return bool(self.attribute(self._state_attr))

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    async def async_update(self) -> None:
        """Update entity from homee."""
        homee = self._entry.runtime_data
        await homee.update_attribute(self._on_off.node_id, self._on_off.id)
