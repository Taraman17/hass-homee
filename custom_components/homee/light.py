"""The homee light platform."""

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.color import (
    brightness_to_value,
    color_hs_to_RGB,
    color_RGB_to_hs,
    value_to_brightness,
)
from pyHomee.const import AttributeType
from pyHomee.model import HomeeNode

from . import HomeeConfigEntry, HomeeNodeEntity, helpers
from .const import LIGHT_PROFILES

_LOGGER = logging.getLogger(__name__)

LIGHT_ATTRIBUTES = [
    AttributeType.COLOR,
    AttributeType.COLOR_MODE,
    AttributeType.COLOR_TEMPERATURE,
    AttributeType.DIMMING_LEVEL,
    AttributeType.HUE,
]


def get_supported_color_modes(node: HomeeNodeEntity) -> set[ColorMode]:
    """Determine the supported color modes from the available attributes."""
    color_modes: set[ColorMode] = set()

    if node.has_attribute(AttributeType.COLOR) or node.has_attribute(AttributeType.HUE):
        color_modes.add(ColorMode.HS)
    if node.has_attribute(AttributeType.COLOR_TEMPERATURE):
        color_modes.add(ColorMode.COLOR_TEMP)

    # if no other color modes are available, set one of those
    if len(color_modes) == 0:
        if node.has_attribute(AttributeType.DIMMING_LEVEL):
            color_modes.add(ColorMode.BRIGHTNESS)
        else:
            color_modes.add(ColorMode.ONOFF)

    return color_modes


def get_color_mode(supported_modes) -> ColorMode:
    """Determine the color mode from the available attributes."""
    if ColorMode.HS in supported_modes:
        return ColorMode.HS
    if ColorMode.COLOR_TEMP in supported_modes:
        return ColorMode.COLOR_TEMP
    if ColorMode.BRIGHTNESS in supported_modes:
        return ColorMode.BRIGHTNESS
    if ColorMode.ONOFF in supported_modes:
        return ColorMode.ONOFF

    return ColorMode.UNKNOWN


def get_light_attribute_sets(
    node: HomeeNodeEntity, index: int
) -> dict[AttributeType, Any]:
    """Return a list with the attributes for each light entity to be created."""
    on_off_attributes = [
        i for i in node.attributes if i.type == AttributeType.ON_OFF and i.editable
    ]

    try:
        target_light = on_off_attributes[index]
    except IndexError:
        return None

    light = {AttributeType.ON_OFF: target_light}
    # go through the next attributes by id until we hit none, on-off or non-light attribute
    # assumption: related homee light attribute ids appear to be sequential
    # e.g. on-off:id1, dimmer:id2, on-off:id3, dimmer:id4
    lookup_offset = 1
    next_id_valid = True
    while next_id_valid:
        attribute_with_next_id = [
            i for i in node.attributes if i.id == (target_light.id + lookup_offset)
        ]
        if not attribute_with_next_id:
            next_id_valid = False
            break
        if attribute_with_next_id[0].type not in LIGHT_ATTRIBUTES:
            next_id_valid = False
            break

        light.update({attribute_with_next_id[0].type: attribute_with_next_id[0]})
        lookup_offset += 1

    return light


def rgb_list_to_decimal(color):
    """Convert an rgb color from list to decimal representation."""
    return int(int(color[0]) << 16) + (int(color[1]) << 8) + (int(color[2]))


def decimal_to_rgb_list(color):
    """Convert an rgb color from decimal to list representation."""
    return [(color & 0xFF0000) >> 16, (color & 0x00FF00) >> 8, (color & 0x0000FF)]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
) -> None:
    """Add the homee platform for the light integration."""

    devices = []
    for node in helpers.get_imported_nodes(config_entry):
        if not is_light_node(node):
            continue
        index = 0
        attributes_exhausted = False
        while not attributes_exhausted:
            light_set = get_light_attribute_sets(node, index)
            if light_set is not None:
                devices.append(HomeeLight(node, light_set, index, config_entry))
                index += 1
            else:
                attributes_exhausted = True

    if devices:
        async_add_devices(devices)


def is_light_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on its profile and attributes."""
    return node.profile in LIGHT_PROFILES and AttributeType.ON_OFF in node.attribute_map


class HomeeLight(HomeeNodeEntity, LightEntity):
    """Representation of a homee light."""

    _attr_has_entity_name = True

    def __init__(
        self, node: HomeeNode, light_set, light_index, entry: HomeeConfigEntry
    ) -> None:
        """Initialize a homee light."""
        HomeeNodeEntity.__init__(self, node, entry)
        self._attr_supported_color_modes = get_supported_color_modes(self)
        self._attr_color_mode = get_color_mode(self._attr_supported_color_modes)
        self._on_off_attr = light_set.get(AttributeType.ON_OFF, None)
        self._dimmer_attr = light_set.get(AttributeType.DIMMING_LEVEL, None)
        self._hue_attr = light_set.get(AttributeType.HUE, None)
        self._col_attr = light_set.get(AttributeType.COLOR, None)
        self._temp_attr = light_set.get(AttributeType.COLOR_TEMPERATURE, None)
        self._mode_attr = light_set.get(AttributeType.COLOR_MODE, None)
        self._light_index = light_index
        self._attr_unique_id = f"{self._node.id}-light-{self._on_off_attr.id}"

    @property
    def name(self):
        """Return the name if set, else a generic name."""
        if self._light_index == 0:
            return None

        return f"light {self._light_index + 1}"

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return value_to_brightness(
            (self._dimmer_attr.minimum + 1, self._dimmer_attr.maximum),
            self._dimmer_attr.current_value,
        )

    @property
    def hs_color(self):
        """Return the color of the light."""
        # Handle color temperature mode
        if self._mode_attr is not None:
            mode = self._mode_attr.current_value

            # Light is in color temperature mode
            if mode == 2:
                return None

        rgb = decimal_to_rgb_list(self._col_attr.current_value)
        return color_RGB_to_hs(rgb[0], rgb[1], rgb[2])

    @property
    def min_color_temp_kelvin(self) -> int | None:
        """Return the min color temperature the light supports."""
        return self._temp_attr.minimum

    @property
    def max_color_temp_kelvin(self) -> int | None:
        """Return the max color temperature the light supports."""
        return self._temp_attr.maximum

    @property
    def color_temp(self):
        """Return the color temperature of the light."""
        return self._temp_attr.current_value

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._on_off_attr.current_value

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if ATTR_BRIGHTNESS in kwargs and self._dimmer_attr is not None:
            target_value = round(
                brightness_to_value(
                    (self._dimmer_attr.minimum, self._dimmer_attr.maximum),
                    kwargs[ATTR_BRIGHTNESS],
                )
            )
            await self.async_set_value_by_id(self._dimmer_attr.id, target_value)
        else:
            # If no brightness value is given, just torn on.
            await self.async_set_value_by_id(self._on_off_attr.id, 1)

        if ATTR_COLOR_TEMP in kwargs and self._temp_attr is not None:
            await self.async_set_value_by_id(
                self._temp_attr.id, kwargs[ATTR_COLOR_TEMP]
            )
        if ATTR_HS_COLOR in kwargs:
            color = kwargs[ATTR_HS_COLOR]
            if self._hue_attr is None:
                await self.async_set_value_by_id(
                    self._col_attr.id,
                    rgb_list_to_decimal(color_hs_to_RGB(*color)),
                )
            elif self._col_attr is None:
                await self.async_set_value_by_id(
                    self._hue_attr.id,
                    rgb_list_to_decimal(color_hs_to_RGB(*color)),
                )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self.async_set_value_by_id(self._on_off_attr.id, 0)
