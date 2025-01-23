"""The homee light platform."""

from typing import Any

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute, HomeeNode

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.util.color import (
    brightness_to_value,
    color_hs_to_RGB,
    color_RGB_to_hs,
    value_to_brightness,
)

from . import HomeeConfigEntry
from .const import LIGHT_PROFILES
from .entity import HomeeNodeEntity
from .helpers import migrate_old_unique_ids

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


def get_light_attribute_sets(node: HomeeNode) -> list[dict[AttributeType, HomeeAttribute]]:
    """Return the lights with their attributes as found in the node."""
    lights: list[dict[AttributeType, HomeeAttribute]] = []
    on_off_attributes = [
        i for i in node.attributes if i.type == AttributeType.ON_OFF and i.editable
    ]
    node_attributes = node.attributes.copy()
    for a in on_off_attributes:
        attribute_dict: dict[AttributeType, HomeeAttribute] = {a.type: a}
        for attribute in node_attributes:
            if attribute.instance == a.instance and attribute.type in LIGHT_ATTRIBUTES:
                attribute_dict[attribute.type] = attribute
                node_attributes.remove(attribute)
        lights.append(attribute_dict)

    return lights


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

    devices: list[HomeeLight] = []
    for node in config_entry.runtime_data.nodes:
        if is_light_node(node):
            light_set = get_light_attribute_sets(node)
            devices.extend(
                HomeeLight(node, light, config_entry)
                for light in light_set
            )

    if devices:
        await migrate_old_unique_ids(hass, devices, Platform.LIGHT)
        async_add_devices(devices)


def is_light_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on its profile and attributes."""
    return node.profile in LIGHT_PROFILES and AttributeType.ON_OFF in node.attribute_map


class HomeeLight(HomeeNodeEntity, LightEntity):
    """Representation of a homee light."""

    def __init__(
        self,
        node: HomeeNode,
        light: dict[AttributeType, HomeeAttribute],
        entry: HomeeConfigEntry,
    ) -> None:
        """Initialize a homee light."""
        super().__init__(node, entry)
        self._attr_supported_color_modes = get_supported_color_modes(self)
        self._attr_color_mode = get_color_mode(self._attr_supported_color_modes)
        self._on_off_attr: HomeeAttribute = light.get(AttributeType.ON_OFF)
        self._dimmer_attr: HomeeAttribute = light.get(AttributeType.DIMMING_LEVEL)
        self._hue_attr: HomeeAttribute = light.get(AttributeType.HUE)
        self._col_attr: HomeeAttribute = light.get(AttributeType.COLOR)
        self._temp_attr: HomeeAttribute = light.get(AttributeType.COLOR_TEMPERATURE)
        self._mode_attr: HomeeAttribute = light.get(AttributeType.COLOR_MODE)
        self._attr_unique_id = (
            f"{entry.runtime_data.settings.uid}-{self._node.id}-{self._on_off_attr.id}"
        )

    @property
    def old_unique_id(self) -> str:
        """Return the old not so unique id of the light entity."""
        return f"{self._node.id}-light-{self._on_off_attr.id}"

    @property
    def name(self) -> str | None:
        """Return a name if more than one light is present."""

        return f"light {self._on_off_attr.instance}" if self._on_off_attr.instance > 0 else None

    @property
    def brightness(self) -> int:
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
        if self._temp_attr is not None:
            return self._temp_attr.minimum

        return None

    @property
    def max_color_temp_kelvin(self) -> int | None:
        """Return the max color temperature the light supports."""
        if self._temp_attr is not None:
            return self._temp_attr.maximum

        return None

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature of the light."""
        if self._temp_attr is not None:
            return self._temp_attr.current_value

        return None

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
            await self.async_set_value(self._dimmer_attr, target_value)
        else:
            # If no brightness value is given, just torn on.
            await self.async_set_value(self._on_off_attr, 1)

        if ATTR_COLOR_TEMP_KELVIN in kwargs and self._temp_attr is not None:
            await self.async_set_value(self._temp_attr, kwargs[ATTR_COLOR_TEMP_KELVIN])
        if ATTR_HS_COLOR in kwargs:
            color = kwargs[ATTR_HS_COLOR]
            if self._hue_attr is None:
                await self.async_set_value(
                    self._col_attr,
                    rgb_list_to_decimal(color_hs_to_RGB(*color)),
                )
            elif self._col_attr is None:
                await self.async_set_value(
                    self._hue_attr,
                    rgb_list_to_decimal(color_hs_to_RGB(*color)),
                )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self.async_set_value(self._on_off_attr, 0)
