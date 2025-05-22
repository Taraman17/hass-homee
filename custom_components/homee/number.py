"""The homee number platform."""

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from . import HomeeConfigEntry
from .const import DOMAIN
from .entity import HomeeEntity
from .helpers import migrate_old_unique_ids

PARALLEL_UPDATES = 0

NUMBER_ATTRIBUTES = {
    AttributeType.BUTTON_BRIGHTNESS_ACTIVE,
    AttributeType.BUTTON_BRIGHTNESS_DIMMED,
    AttributeType.DISPLAY_BRIGHTNESS_ACTIVE,
    AttributeType.DISPLAY_BRIGHTNESS_DIMMED,
    AttributeType.CURRENT_VALVE_POSITION,
    AttributeType.DOWN_POSITION,
    AttributeType.DOWN_SLAT_POSITION,
    AttributeType.DOWN_TIME,
    AttributeType.ENDPOSITION_CONFIGURATION,
    AttributeType.EXTERNAL_TEMPERATURE_OFFSET,
    AttributeType.FLOOR_TEMPERATURE_OFFSET,
    AttributeType.MOTION_ALARM_CANCELATION_DELAY,
    AttributeType.OPEN_WINDOW_DETECTION_SENSIBILITY,
    AttributeType.POLLING_INTERVAL,
    AttributeType.SHUTTER_SLAT_TIME,
    AttributeType.SLAT_MAX_ANGLE,
    AttributeType.SLAT_MIN_ANGLE,
    AttributeType.SLAT_STEPS,
    AttributeType.TEMPERATURE_OFFSET,
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

    if attribute.type == AttributeType.BUTTON_BRIGHTNESS_ACTIVE:
        translation_key = "number_button_brightness_active"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.BUTTON_BRIGHTNESS_DIMMED:
        translation_key = "number_button_brightness_dimmed"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.DISPLAY_BRIGHTNESS_ACTIVE:
        translation_key = "number_display_brightness_active"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.DISPLAY_BRIGHTNESS_DIMMED:
        translation_key = "number_display_brightness_dimmed"
        entity_category = EntityCategory.CONFIG

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

    if attribute.type == AttributeType.EXTERNAL_TEMPERATURE_OFFSET:
        translation_key = "number_external_temperature_offset"
        entity_category = EntityCategory.CONFIG

    if attribute.type == AttributeType.FLOOR_TEMPERATURE_OFFSET:
        translation_key = "number_floor_temperature_offset"
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

    if attribute.type == AttributeType.TEMPERATURE_REPORT_INTERVAL:
        device_class = NumberDeviceClass.DURATION
        translation_key = "number_temperature_report_interval"
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
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeNumber(attribute, config_entry)
            for attribute in node.attributes
            if attribute.type in NUMBER_ATTRIBUTES and attribute.data != "fixed_value"
        )
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.NUMBER)
        async_add_devices(devices)


class HomeeNumber(HomeeEntity, NumberEntity):
    """Representation of a homee number."""

    def __init__(
        self,
        attribute: HomeeAttribute,
        entry: HomeeConfigEntry,
    ) -> None:
        """Initialize a homee number entity."""
        super().__init__(attribute, entry)
        (
            self._attr_device_class,
            self._attr_translation_key,
            self._attr_entity_category,
        ) = get_device_properties(attribute)
        self._attr_native_min_value = attribute.minimum
        self._attr_native_max_value = attribute.maximum
        self._attr_native_step = attribute.step_value

        if self.translation_key is None:
            self._attr_name = None

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the number entity."""
        return f"{self._attribute.node_id}-number-{self._attribute.id}"

    @property
    def available(self) -> bool:
        """Return the availability of the underlying node."""
        return super().available and self._attribute.editable

    @property
    def native_value(self) -> int:
        """Return the native value of the sensor."""
        # TODO: If HA supports klx as unit, remove.
        if self._attribute.unit == "klx":
            return int(self._attribute.current_value) * 1000

        return int(self._attribute.current_value)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the native unit of the number entity."""
        if self._attribute.unit == "n/a":
            return ""

        # TODO: If HA supports klx as unit, remove.
        if self._attribute.unit == "klx":
            return "lx"

        return self._attribute.unit

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if self._attribute.editable:
            await self._entry.runtime_data.set_value(
                self._attribute.node_id, self._attribute.id, value
            )
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_editable",
                translation_placeholders={"entity": str(self.name)},
            )
