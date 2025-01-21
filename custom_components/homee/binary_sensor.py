"""The homee binary sensor platform."""

import logging

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant

from . import HomeeConfigEntry
from .entity import HomeeEntity
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
    device_class = None
    translation_key = ""
    entity_category = None

    if attribute.type == AttributeType.BATTERY_LOW_ALARM:
        device_class = BinarySensorDeviceClass.BATTERY
        translation_key = "battery_low_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.FLOOD_ALARM:
        device_class = BinarySensorDeviceClass.MOISTURE
        translation_key = "flood_sensor"

    if attribute.type == AttributeType.HIGH_TEMPERATURE_ALARM:
        device_class = BinarySensorDeviceClass.HEAT
        translation_key = "heat_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.LOAD_ALARM:
        translation_key = "load_alarm_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.LOCK_STATE:
        device_class = BinarySensorDeviceClass.LOCK
        translation_key = "lock_sensor"

    if attribute.type == AttributeType.MALFUNCTION_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "malfunction_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.MAXIMUM_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "maximum_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.MINIMUM_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "minimum_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.MOTION_ALARM:
        device_class = BinarySensorDeviceClass.MOTION
        translation_key = "motion_sensor"

    if attribute.type == AttributeType.ON_OFF:
        device_class = BinarySensorDeviceClass.PLUG
        translation_key = "plug_sensor"

    if attribute.type == AttributeType.OPEN_CLOSE:
        device_class = BinarySensorDeviceClass.OPENING
        translation_key = "opening_sensor"

    if attribute.type == AttributeType.OVER_CURRENT_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "overcurrent_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.OVERLOAD_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "overload_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.PRESENCE_ALARM:
        device_class = BinarySensorDeviceClass.MOTION
        translation_key = "motion_sensor"

    if attribute.type == AttributeType.RAIN_FALL:
        device_class = BinarySensorDeviceClass.MOISTURE
        translation_key = "rain_sensor"

    if attribute.type == AttributeType.SMOKE_ALARM:
        device_class = BinarySensorDeviceClass.SMOKE
        translation_key = "smoke_sensor"

    if attribute.type == AttributeType.SURGE_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "surge_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.TAMPER_ALARM:
        device_class = BinarySensorDeviceClass.TAMPER
        translation_key = "tamper_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    if attribute.type == AttributeType.VOLTAGE_DROP_ALARM:
        device_class = BinarySensorDeviceClass.PROBLEM
        translation_key = "voltage_drop_sensor"
        entity_category = EntityCategory.DIAGNOSTIC

    return (device_class, translation_key, entity_category)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
) -> None:
    """Add the homee platform for the binary sensor integration."""

    devices = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeBinarySensor(attribute, config_entry)
            for attribute in node.attributes
            if (
                attribute.type in HOMEE_BINARY_SENSOR_ATTRIBUTES
                and not attribute.editable
            )
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.BINARY_SENSOR)
        async_add_devices(devices)


class HomeeBinarySensor(HomeeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        binary_sensor_attribute: HomeeAttribute,
        entry: HomeeConfigEntry,
    ) -> None:
        """Initialize a homee binary sensor entity."""
        HomeeEntity.__init__(self, binary_sensor_attribute, entry)

        self._configure_device_class()
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._attribute.node_id}-{self._attribute.id}"
        )

    def _configure_device_class(self):
        """Configure the device class of the sensor."""

        # Get the initial device class and state attribute
        (
            self._device_class,
            self._attr_translation_key,
            self._attr_entity_category,
        ) = get_device_class(self._attribute)

        if self.translation_key is None:
            self._attr_name = None

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._attribute.node_id}-binary_sensor-{self._attribute.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return bool(self._attribute.get_value())

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    async def async_update(self) -> None:
        """Update entity from homee."""
        homee = self._entry.runtime_data
        await homee.update_attribute(self._attribute.node_id, self._attribute.id)
