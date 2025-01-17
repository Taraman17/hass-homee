"""The homee number platform."""

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from . import HomeeConfigEntry, helpers
from .const import DOMAIN
from .entity import HomeeNodeEntity
from .helpers import migrate_old_unique_ids

NUMBER_ATTRIBUTES = {
    AttributeType.CURRENT_VALVE_POSITION,
    AttributeType.DOWN_POSITION,
    AttributeType.DOWN_SLAT_POSITION,
    AttributeType.DOWN_TIME,
    AttributeType.ENDPOSITION_CONFIGURATION,
    AttributeType.MOTION_ALARM_CANCELATION_DELAY,
    AttributeType.OPEN_WINDOW_DETECTION_SENSIBILITY,
    AttributeType.POLLING_INTERVAL,
    AttributeType.SHUTTER_SLAT_TIME,
    AttributeType.SLAT_MAX_ANGLE,
    AttributeType.SLAT_MIN_ANGLE,
    AttributeType.SLAT_STEPS,
    AttributeType.TEMPERATURE_OFFSET,
    AttributeType.UP_TIME,
    AttributeType.WAKE_UP_INTERVAL,
    AttributeType.WIND_MONITORING_STATE,
}


def get_device_properties(attribute: HomeeAttribute):
    """Determinde the device properties based on the attribute."""
    device_class = None
    translation_key = None
    entity_category = None

    if attribute.type == AttributeType.CURRENT_VALVE_POSITION:
        translation_key = "number_valve_position"

    if attribute.type == AttributeType.DOWN_POSITION:
        translation_key = "number_down_position"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.DOWN_SLAT_POSITION:
        translation_key = "number_down_slat_position"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.DOWN_TIME:
        device_class = NumberDeviceClass.DURATION
        translation_key = "number_down_time"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.ENDPOSITION_CONFIGURATION:
        translation_key = "number_endposition_configuration"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.MOTION_ALARM_CANCELATION_DELAY:
        translation_key = "number_motion_alarm_cancelation_delay"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.OPEN_WINDOW_DETECTION_SENSIBILITY:
        translation_key = "number_open_window_detection_sensibility"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.POLLING_INTERVAL:
        translation_key = "number_polling_interval"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.SHUTTER_SLAT_TIME:
        device_class = NumberDeviceClass.DURATION
        translation_key = "number_shutter_slat_time"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.SLAT_MAX_ANGLE:
        translation_key = "number_slat_max_angle"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.SLAT_MIN_ANGLE:
        translation_key = "number_slat_min_angle"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.SLAT_STEPS:
        translation_key = "number_slat_steps"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.TEMPERATURE_OFFSET:
        device_class = NumberDeviceClass.TEMPERATURE
        translation_key = "number_temperature_offset"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.UP_TIME:
        device_class = NumberDeviceClass.DURATION
        translation_key = "number_up_time"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.WAKE_UP_INTERVAL:
        translation_key = "number_wake_up_interval"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.WIND_MONITORING_STATE:
        translation_key = "number_wind_monitoring_state"
        entity_category = EntityCategory.CONFIG

    return (device_class, translation_key, entity_category)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
):
    """Add the homee platform for the number components."""

    devices = []
    for node in helpers.get_imported_nodes(config_entry):
        devices.extend(
            HomeeNumber(node, config_entry, attribute)
            for attribute in node.attributes
            if attribute.type in NUMBER_ATTRIBUTES
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.NUMBER)
        async_add_devices(devices)


class HomeeNumber(HomeeNodeEntity, NumberEntity):
    """Representation of a homee number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: HomeeConfigEntry,
        number_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee number entity."""
        HomeeNodeEntity.__init__(self, node, entry)
        self._number = number_attribute
        (
            self._attr_device_class,
            self._attr_translation_key,
            self._attr_entity_category,
        ) = get_device_properties(number_attribute)
        self._attr_native_min_value = number_attribute.minimum
        self._attr_native_max_value = number_attribute.maximum
        self._attr_native_step = number_attribute.step_value

        if self.translation_key is None:
            self._attr_name = None

        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._node.id}-{self._number.id}"
        )

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._node.id}-number-{self._number.id}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._number.editable

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        # TODO: If HA supports klx as unit, remove.
        if self._number.unit == "klx":
            return self._number.current_value * 1000

        return self._number.current_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the native unit of the number entity."""
        if self._number.unit == "n/a":
            return None

        # TODO: If HA supports klx as unit, remove.
        if self._number.unit == "klx":
            return "lx"

        return self._number.unit

    async def async_update(self) -> None:
        """Update entity from homee."""
        homee = self._entry.runtime_data
        await homee.update_attribute(self._number.node_id, self._number.id)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if self._number.editable:
            await self.async_set_value_by_id(self._number.id, value)
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_editable",
                translation_placeholders={"entity": self.name},
            )
