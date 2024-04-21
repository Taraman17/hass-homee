"""The homee climate platform."""

import logging

from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    PRESET_BOOST,
    PRESET_SLEEP,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

HOMEE_UNIT_TO_HA_UNIT = {
    "°C": UnitOfTemperature.CELSIUS,
    "°F": UnitOfTemperature.FAHRENHEIT,
}


def get_climate_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported climate features of a homee node based on the available attributes."""
    features = default

    if node.has_attribute(AttributeType.TARGET_TEMPERATURE):
        features |= ClimateEntityFeature.TARGET_TEMPERATURE

    if node.has_attribute(AttributeType.HEATING_MODE):
        features |= ClimateEntityFeature.TURN_ON
        features |= ClimateEntityFeature.TURN_OFF

    if node.get_attribute(AttributeType.HEATING_MODE).maximum > 1:
        # Node supports more modes than on and off
        features |= ClimateEntityFeature.PRESET_MODE

    return features


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the light integration."""
    # homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_climate_node(node):
            continue
        devices.append(HomeeClimate(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_climate_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on it's profile and attributes."""
    return node.profile in [
        NodeProfile.HEATING_SYSTEM,
        NodeProfile.RADIATOR_THERMOSTAT,
        NodeProfile.ROOM_THERMOSTAT,
        NodeProfile.ROOM_THERMOSTAT_WITH_HUMIDITY_SENSOR,
        NodeProfile.THERMOSTAT_WITH_HEATING_AND_COOLING,
        NodeProfile.WIFI_RADIATOR_THERMOSTAT,
        NodeProfile.WIFI_ROOM_THERMOSTAT,
    ]


class HomeeClimate(HomeeNodeEntity, ClimateEntity):
    """Representation of a homee climate device."""

    _attr_has_entity_name = True
    _attr_name = None

    # TODO: remove after release of HA 2025.01
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, node: HomeeNode, entry: ConfigEntry) -> None:
        """Initialize a homee climate entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_climate_features(self)
        self._attr_preset_modes = [PRESET_BOOST, PRESET_SLEEP]
        self._attr_target_temperature_step = self.get_attribute(
            AttributeType.TARGET_TEMPERATURE
        ).step_value
        self._attr_unique_id = f"{self._node.id}-climate"

    @property
    def supported_features(self) -> list[ClimateEntityFeature]:
        """Return the supported features of the entity."""
        return self._supported_features

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the temperature unit of the device."""
        return HOMEE_UNIT_TO_HA_UNIT[self.get_attribute(AttributeType.TEMPERATURE).unit]

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the available hvac operation modes."""
        return [HVACMode.OFF, HVACMode.HEAT]

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the hvac operation mode."""
        if self._node.profile in (
            NodeProfile.RADIATOR_THERMOSTAT,
            NodeProfile.WIFI_RADIATOR_THERMOSTAT,
        ):
            if self.get_attribute(AttributeType.HEATING_MODE).current_value == 0:
                return HVACMode.OFF

        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return the hvac action."""
        if self._node.profile in (
            NodeProfile.RADIATOR_THERMOSTAT,
            NodeProfile.WIFI_RADIATOR_THERMOSTAT,
        ):
            if self.get_attribute(AttributeType.HEATING_MODE).current_value == 0:
                return HVACAction.OFF

            if self.attribute(AttributeType.CURRENT_VALVE_POSITION) > 0:
                return HVACAction.HEATING

        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str:
        """Return the present preset mode."""
        if self.attribute(AttributeType.HEATING_MODE) == 2:
            return PRESET_SLEEP
        if self.attribute(AttributeType.HEATING_MODE) == 3:
            return PRESET_BOOST

        return None

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self.attribute(AttributeType.TEMPERATURE)

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self.attribute(AttributeType.TARGET_TEMPERATURE)

    @property
    def min_temp(self) -> float:
        """Return the lowest settable target temperature."""
        if self.has_attribute(AttributeType.TARGET_TEMPERATURE_LOW):
            return self.attribute(AttributeType.TARGET_TEMPERATURE_LOW)

        return self.get_attribute(AttributeType.TARGET_TEMPERATURE).minimum

    @property
    def max_temp(self) -> float:
        """Return the lowest settable target temperature."""
        if self.has_attribute(AttributeType.TARGET_TEMPERATURE_HIGH):
            return self.attribute(AttributeType.TARGET_TEMPERATURE_HIGH)

        return self.get_attribute(AttributeType.TARGET_TEMPERATURE).maximum

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        mode = 0
        if hvac_mode == HVACMode.HEAT:
            mode = 1

        await self.async_set_value(AttributeType.HEATING_MODE, mode)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if preset_mode == PRESET_SLEEP:
            preset = 2
        elif preset_mode == PRESET_BOOST:
            preset = 3

        self.async_set_value(AttributeType.HEATING_MODE, preset)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""

        if ATTR_TEMPERATURE in kwargs:
            await self.async_set_value(
                AttributeType.TARGET_TEMPERATURE, kwargs[ATTR_TEMPERATURE]
            )

    async def async_turn_on(self):
        """Turn the entity on."""
        await self.async_set_value(AttributeType.HEATING_MODE, 1)

    async def async_turn_off(self):
        """Turn the entity on."""
        await self.async_set_value(AttributeType.HEATING_MODE, 0)
