"""The homee number platform."""

from pymee.const import AttributeType
from pymee.model import HomeeAttribute, HomeeNode

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import HomeeNodeEntity, helpers

NUMBER_ATTRIBUTES = {
    AttributeType.DOWN_POSITION,
    AttributeType.ENDPOSITION_CONFIGURATION,
    AttributeType.MOTION_ALARM_CANCELATION_DELAY,
    AttributeType.POLLING_INTERVAL,
    AttributeType.TARGET_TEMPERATURE,
    AttributeType.WAKE_UP_INTERVAL,
    AttributeType.WIND_MONITORING_STATE,
}


def get_device_properties(attribute: HomeeAttribute):
    """Determinde the device properties based on the attribute."""
    device_class = None
    translation_key = None

    if attribute.type == AttributeType.DOWN_POSITION:
        translation_key = "number_down_position"

    if attribute.type == AttributeType.ENDPOSITION_CONFIGURATION:
        translation_key = "number_endposition_configuration"

    if attribute.type == AttributeType.MOTION_ALARM_CANCELATION_DELAY:
        translation_key = "number_motion_alarm_cancelation_delay"

    if attribute.type == AttributeType.POLLING_INTERVAL:
        translation_key = "number_polling_interval"

    if attribute.type == AttributeType.TARGET_TEMPERATURE:
        device_class = NumberDeviceClass.TEMPERATURE
        translation_key = "number_target_temperature"

    if attribute.type == AttributeType.WAKE_UP_INTERVAL:
        translation_key = "number_wake_up_interval"

    if attribute.type == AttributeType.WIND_MONITORING_STATE:
        translation_key = "number_wind_monitoring_state"

    return (device_class, translation_key)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the number components."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        for attribute in node.attributes:
            if attribute.type in NUMBER_ATTRIBUTES and attribute.editable:
                devices.append(HomeeNumber(node, config_entry, attribute))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeNumber(HomeeNodeEntity, NumberEntity):
    """Representation of a homee number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        number_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee number entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._number = number_attribute
        self._attr_device_class, self._attr_translation_key = get_device_properties(
            number_attribute
        )
        self._attr_native_min_value = number_attribute.minimum
        self._attr_native_max_value = number_attribute.maximum
        self._attr_native_step = number_attribute.step_value
        self._attr_native_value = number_attribute.current_value
        self._attr_native_unit_of_measurement = number_attribute.unit

        if self.translation_key is None:
            self._attr_name = None

        self._attr_unique_id = f"{self._node.id}-number-{self._number.id}"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.async_set_value_by_id(self._number.id, value)
