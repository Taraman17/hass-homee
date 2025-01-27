"""The homee climate platform."""

from typing import Any
from pyHomee.const import AttributeType, NodeProfile
from pyHomee.model import HomeeNode

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeeConfigEntry
from .const import CLIMATE_PROFILES, DOMAIN, PRESET_MANUAL
from .entity import HomeeNodeEntity
from .helpers import migrate_old_unique_ids

HOMEE_UNIT_TO_HA_UNIT = {
    "°C": UnitOfTemperature.CELSIUS,
    "°F": UnitOfTemperature.FAHRENHEIT,
}

ROOM_THERMOSTATS = {
    NodeProfile.ROOM_THERMOSTAT,
    NodeProfile.ROOM_THERMOSTAT_WITH_HUMIDITY_SENSOR,
    NodeProfile.WIFI_ROOM_THERMOSTAT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomeeConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Add the homee platform for the climate integration."""

    devices = [
        HomeeClimate(node, config_entry)
        for node in config_entry.runtime_data.nodes
        if is_climate_node(node)
    ]
    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.CLIMATE)
        async_add_devices(devices)


def is_climate_node(node: HomeeNode) -> bool:
    """Determine if a node is controllable as a climate device based on it's profile."""
    return node.profile in CLIMATE_PROFILES


class HomeeClimate(HomeeNodeEntity, ClimateEntity):
    """Representation of a homee climate device."""

    _attr_name = None
    _attr_translation_key = DOMAIN

    def __init__(self, node: HomeeNode, entry: HomeeConfigEntry) -> None:
        """Initialize a homee climate entity."""
        HomeeNodeEntity.__init__(self, node, entry)
        (
            self._attr_supported_features,
            self._attr_hvac_modes,
            self._attr_preset_modes,
        ) = get_climate_features(self)
        self._traget_temp = self._node.get_attribute_by_type(
            AttributeType.TARGET_TEMPERATURE
        )
        assert self._traget_temp is not None
        self._attr_target_temperature_step = self._traget_temp.step_value
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._node.id}-{self._traget_temp.id}"
        )

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the climate entity."""
        return f"{self._node.id}-climate"

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the temperature unit of the device."""
        assert self._traget_temp is not None
        return HOMEE_UNIT_TO_HA_UNIT[self._traget_temp.unit]

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the hvac operation mode."""
        if ClimateEntityFeature.TURN_OFF in self.supported_features and (
            (attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE))
            is not None
        ):
            if attribute.current_value == 0:
                return HVACMode.OFF

        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return the hvac action."""
        if ClimateEntityFeature.TURN_OFF in self.supported_features and (
            (attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE))
            is not None
        ):
            if attribute.current_value == 0:
                return HVACAction.OFF

        if (
            attribute := self._node.get_attribute_by_type(
                AttributeType.CURRENT_VALVE_POSITION
            )
        ) is not None:
            if attribute.current_value == 0:
                return HVACAction.IDLE

        if (
            self.current_temperature
            and self.current_temperature >= self.target_temperature
        ):
            return HVACAction.IDLE

        return HVACAction.HEATING

    @property
    def preset_mode(self) -> str:
        """Return the present preset mode."""
        if (
            ClimateEntityFeature.PRESET_MODE in self.supported_features
            and (
                attribute := self._node.get_attribute_by_type(
                    AttributeType.HEATING_MODE
                )
            )
            is not None
        ):
            if attribute.current_value == 2:
                return PRESET_ECO
            if attribute.current_value == 3:
                return PRESET_BOOST
            if attribute.current_value == 4:
                return PRESET_MANUAL

        return PRESET_NONE

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if (
            temp := self._node.get_attribute_by_type(AttributeType.TEMPERATURE)
        ) is not None:
            return temp.current_value
        return None

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        assert self._traget_temp is not None
        return self._traget_temp.current_value

    @property
    def min_temp(self) -> float:
        """Return the lowest settable target temperature."""
        if (
            attribute := self._node.get_attribute_by_type(
                AttributeType.TARGET_TEMPERATURE_LOW
            )
        ) is not None:
            return attribute.current_value

        assert self._traget_temp is not None
        return self._traget_temp.minimum

    @property
    def max_temp(self) -> float:
        """Return the lowest settable target temperature."""
        if (
            attribute := self._node.get_attribute_by_type(
                AttributeType.TARGET_TEMPERATURE_HIGH
            )
        ) is not None:
            return attribute.current_value

        assert self._traget_temp is not None
        return self._traget_temp.maximum

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # Currently only HEAT and OFF are supported.
        mode = 0
        if hvac_mode == HVACMode.HEAT:
            mode = 1

        if (
            attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE)
        ) is not None:
            await self.async_set_value(attribute, mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new target preset mode."""
        preset = 0
        if preset_mode == PRESET_NONE:
            preset = 1
        if preset_mode == PRESET_ECO:
            preset = 2
        elif preset_mode == PRESET_BOOST:
            preset = 3
        elif preset_mode == PRESET_MANUAL:
            preset = 4

        if (
            attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE)
        ) is not None:
            await self.async_set_value(attribute, preset)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""

        assert self._traget_temp is not None
        if ATTR_TEMPERATURE in kwargs:
            await self.async_set_value(self._traget_temp, kwargs[ATTR_TEMPERATURE])

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        if (
            attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE)
        ) is not None:
            await self.async_set_value(attribute, 1)

    async def async_turn_off(self) -> None:
        """Turn the entity on."""
        if (
            attribute := self._node.get_attribute_by_type(AttributeType.HEATING_MODE)
        ) is not None:
            await self.async_set_value(attribute, 0)


def get_climate_features(
    node: HomeeClimate,
) -> tuple[ClimateEntityFeature, list[HVACMode], list[str] | None]:
    """Determine supported climate features of a node based on the available attributes."""
    features = ClimateEntityFeature.TARGET_TEMPERATURE
    hvac_modes = [HVACMode.HEAT]
    preset_modes: list[str] = []

    if node.has_attribute(AttributeType.HEATING_MODE):
        features |= ClimateEntityFeature.TURN_ON
        features |= ClimateEntityFeature.TURN_OFF
        hvac_modes.append(HVACMode.OFF)

        if (
            attribute := node._node.get_attribute_by_type(AttributeType.HEATING_MODE)
        ) is not None and attribute.maximum > 1:
            # Node supports more modes than off and heating.
            features |= ClimateEntityFeature.PRESET_MODE
            preset_modes.extend([PRESET_BOOST, PRESET_ECO, PRESET_MANUAL])

    if len(preset_modes) > 0:
        preset_modes.append(PRESET_NONE)
    return (features, hvac_modes, preset_modes if len(preset_modes) > 0 else None)
