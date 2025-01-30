"""The homee binary sensor platform."""

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

BINARY_SENSOR_DESCRIPTIONS: dict[AttributeType, BinarySensorEntityDescription] = {
    AttributeType.BATTERY_LOW_ALARM: BinarySensorEntityDescription(
        key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.BLACKOUT_ALARM: BinarySensorEntityDescription(
        key="blackout_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.CO2ALARM: BinarySensorEntityDescription(
        key="carbon_dioxide",
        device_class=BinarySensorDeviceClass.GAS
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
    AttributeType.LEAK_ALARM: BinarySensorEntityDescription(
        key="leak_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
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
    AttributeType.LOW_TEMPERATURE_ALARM: BinarySensorEntityDescription(
        key="low_temperature_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    AttributeType.MOTOR_BLOCKED_ALARM: BinarySensorEntityDescription(
        key="motor_blocked_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    AttributeType.POWER_SUPPLY_ALARM: BinarySensorEntityDescription(
        key="power_supply_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.RAIN_FALL: BinarySensorEntityDescription(
        key="rain",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    AttributeType.REPLACE_FILTER_ALARM: BinarySensorEntityDescription(
        key="replace_filter",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AttributeType.SMOKE_ALARM: BinarySensorEntityDescription(
        key="smoke",
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    AttributeType.STORAGE_ALARM: BinarySensorEntityDescription(
        key="storage_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    AttributeType.WATER_ALARM: BinarySensorEntityDescription(
        key="water_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomeeConfigEntry,
    async_add_devices: AddEntitiesCallback,
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
