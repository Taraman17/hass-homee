"""The homee cover platform."""

import logging
from typing import cast

from homeassistant.core import HomeAssistant
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntityFeature,
    CoverEntity,
    CoverDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

OPEN_CLOSE_ATTRIBUTES = [
    AttributeType.OPEN_CLOSE,
    AttributeType.SLAT_ROTATION_IMPULSE,
    AttributeType.UP_DOWN,
]
POSITION_ATTRIBUTES = [AttributeType.POSITION, AttributeType.SHUTTER_SLAT_POSITION]


def get_cover_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported cover features of a homee node based on the available attributes."""
    features = default

    for attribute in node.attributes:
        if attribute.type in OPEN_CLOSE_ATTRIBUTES:
            if attribute.editable:
                features |= CoverEntityFeature.OPEN
                features |= CoverEntityFeature.CLOSE
                features |= CoverEntityFeature.STOP

        if attribute.type in POSITION_ATTRIBUTES:
            if attribute.editable:
                features |= CoverEntityFeature.SET_POSITION

    return features


def get_device_class(node: HomeeNode) -> int:
    """Determine the device class a homee node based on the node profile."""
    if node.profile == NodeProfile.GARAGE_DOOR_OPERATOR:
        return CoverDeviceClass.GARAGE

    if node.profile == NodeProfile.SHUTTER_POSITION_SWITCH:
        return CoverDeviceClass.SHUTTER

    return None


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the cover integration."""
    # homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_cover_node(node):
            continue
        devices.append(HomeeCover(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_cover_node(node: HomeeNode):
    """Determine if a node is controllable as a homee cover based on its profile and attributes."""
    return node.profile in [
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH,
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH_WITHOUT_SLAT_POSITION,
        NodeProfile.GARAGE_DOOR_OPERATOR,
        NodeProfile.SHUTTER_POSITION_SWITCH,
    ]


class HomeeCover(HomeeNodeEntity, CoverEntity):
    """Representation of a homee cover device."""

    _attr_has_entity_name = True

    def __init__(self, node: HomeeNode, entry: ConfigEntry) -> None:
        """Initialize a homee cover entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_cover_features(node)
        self._device_class = get_device_class(node)

        self._attr_unique_id = f"{self._node.id}-cover"

        # TODO needs to be changed, when covers with tilt should be supported
        # For now there should only be one of these.
        if self.has_attribute(AttributeType.OPEN_CLOSE):
            self._open_close_attribute = AttributeType.OPEN_CLOSE
        elif self.has_attribute(AttributeType.SLAT_ROTATION_IMPULSE):
            self._open_close_attribute = AttributeType.SLAT_ROTATION_IMPULSE
        else:  # UP_DOWN is default
            self._open_close_attribute = AttributeType.UP_DOWN

        # Set position can also be controlled with different attributes.
        if self.has_attribute(AttributeType.POSITION):
            # POSITION is default.
            self._position_attribute = AttributeType.POSITION
        else:
            self._position_attribute = AttributeType.SHUTTER_SLAT_POSITION

    @property
    def name(self):
        """Return the display name of this cover."""
        return None

    @property
    def supported_features(self):
        """Return the supported features of the entity."""
        return self._supported_features

    @property
    def current_cover_position(self):
        """Return the cover's position."""
        # Translate the homee position values to HA's 0-100 scale
        homee_min = self.get_attribute(self._position_attribute).minimum
        homee_max = self.get_attribute(self._position_attribute).maximum
        homee_position = self.attribute(self._position_attribute)
        position = ((homee_position - homee_min) / (homee_max - homee_min)) * 100

        return 100 - position

    @property
    def is_opening(self):
        """Return the opening status of the cover."""
        return self.attribute(self._open_close_attribute) == 3

    @property
    def is_closing(self):
        """Return the closing status of the cover."""
        return self.attribute(self._open_close_attribute) == 4

    @property
    def is_closed(self):
        """Return the state of the cover."""
        # TODO: Not sure if the open_close reverse option really has effect
        #       here. The tested device showed 100% as open however.
        if self.get_attribute(self._open_close_attribute).options.reverse_control_ui:
            return (
                self.attribute(self._position_attribute)
                == self.get_attribute(self._position_attribute).minimum
            )

        return (
            self.attribute(self._position_attribute)
            == self.get_attribute(self._position_attribute).maximum
        )

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        open_close = self._open_close_attribute
        if open_close == AttributeType.SLAT_ROTATION_IMPULSE:
            # For now, we only know of one device that uses this Attribute.
            # For other devices the commands may be different.
            await self.async_set_value(open_close, 2)
        else:
            if self.get_attribute(open_close).options.reverse_control_ui:
                await self.async_set_value(open_close, 1)
            else:
                await self.async_set_value(open_close, 0)

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        # For now, all devices use 1 as close here.
        open_close = self._open_close_attribute
        if self.get_attribute(open_close).options.reverse_control_ui:
            await self.async_set_value(open_close, 0)
        else:
            await self.async_set_value(open_close, 1)

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if CoverEntityFeature.SET_POSITION in self._supported_features:
            position = 100 - cast(int, kwargs[ATTR_POSITION])

            # Convert position to range of our entity.
            homee_min = self.get_attribute(self._position_attribute).minimum
            homee_max = self.get_attribute(self._position_attribute).maximum
            homee_position = (position / 100) * (homee_max - homee_min) + homee_min

            await self.async_set_value(self._position_attribute, homee_position)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        if self._open_close_attribute != AttributeType.SLAT_ROTATION_IMPULSE:
            # The SLAT_ROTATION_IMPULSE does not support stop.
            await self.async_set_value(self._open_close_attribute, 2)
