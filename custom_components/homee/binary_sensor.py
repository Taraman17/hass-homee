"""The homee binary sensor platform."""

import logging

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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


BINARY_SENSOR_DESCRIPTIONS: dict[AttributeType, BinarySensorEntityDescription] = {
    AttributeType.BATTERY_LOW_ALARM: BinarySensorEntityDescription(
        key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.FLOOD_ALARM: BinarySensorEntityDescription(
        key="flood",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    AttributeType.HIGH_TEMPERATURE_ALARM: BinarySensorEntityDescription(
        key="heat",
        device_class=BinarySensorDeviceClass.HEAT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.LOAD_ALARM: BinarySensorEntityDescription(
        key="load_alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.LOCK_STATE: BinarySensorEntityDescription(
        key="lock",
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    AttributeType.MALFUNCTION_ALARM: BinarySensorEntityDescription(
        key="malfunction",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.MAXIMUM_ALARM: BinarySensorEntityDescription(
        key="maximum",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.MINIMUM_ALARM: BinarySensorEntityDescription(
        key="minimum",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.MOTION_ALARM: BinarySensorEntityDescription(
        key="motion",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    AttributeType.ON_OFF: BinarySensorEntityDescription(
        key="plug",
        device_class=BinarySensorDeviceClass.PLUG,
    ),
    AttributeType.OPEN_CLOSE: BinarySensorEntityDescription(
        key="opening",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    AttributeType.OVER_CURRENT_ALARM: BinarySensorEntityDescription(
        key="overcurrent",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.OVERLOAD_ALARM: BinarySensorEntityDescription(
        key="overload",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.PRESENCE_ALARM: BinarySensorEntityDescription(
        key="motion",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    AttributeType.RAIN_FALL: BinarySensorEntityDescription(
        key="rain",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    AttributeType.SMOKE_ALARM: BinarySensorEntityDescription(
        key="smoke",
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    AttributeType.SURGE_ALARM: BinarySensorEntityDescription(
        key="surge",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.TAMPER_ALARM: BinarySensorEntityDescription(
        key="tamper",
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.VOLTAGE_DROP_ALARM: BinarySensorEntityDescription(
        key="voltage_drop",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Add the homee platform for the binary sensor integration."""

    devices: list[HomeeBinarySensor] = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeBinarySensor(
                attribute, config_entry, BINARY_SENSOR_DESCRIPTIONS[attribute.type]
            )
            for attribute in node.attributes
            if attribute.type in BINARY_SENSOR_DESCRIPTIONS and not attribute.editable
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.BINARY_SENSOR)
        async_add_devices(devices)


class HomeeBinarySensor(HomeeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    def __init__(
        self,
        attribute: HomeeAttribute,
        entry: HomeeConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize a homee binary sensor entity."""
        super().__init__(attribute, entry)

        self.entity_description = description
        self._attr_translation_key = description.key

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the binary-sensor entity."""
        return f"{self._attribute.node_id}-binary_sensor-{self._attribute.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return bool(self._attribute.get_value())
