"""The homee light platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import (
    color_hs_to_RGB,
    color_RGB_to_hs,
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers
from .const import HOMEE_LIGHT_MAX_MIRED, HOMEE_LIGHT_MIN_MIRED

_LOGGER = logging.getLogger(__name__)

LIGHT_ATTRIBUTES = [
    AttributeType.COLOR,
    AttributeType.COLOR_MODE,
    AttributeType.COLOR_TEMPERATURE,
    AttributeType.DIMMING_LEVEL,
    AttributeType.HUE,
]


def get_light_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported features of a homee light based on the available attributes."""
    features = default

    if node.has_attribute(AttributeType.DIMMING_LEVEL):
        features |= ColorMode.BRIGHTNESS
    if node.has_attribute(AttributeType.COLOR) or node.has_attribute(AttributeType.HUE):
        features |= ColorMode.HS
    if node.has_attribute(AttributeType.COLOR_TEMPERATURE):
        features |= ColorMode.COLOR_TEMP

    return features


def get_light_attribute_sets(node: HomeeNodeEntity, index: int):
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
        else:
            light.update({attribute_with_next_id[0].type: attribute_with_next_id[0]})
            lookup_offset += 1

    return light


def rgb_list_to_decimal(color):
    """Convert an rgb color from list to decimal representation."""
    return int(int(color[0]) << 16) + (int(color[1]) << 8) + (int(color[2]))


def decimal_to_rgb_list(color):
    """Convert an rgb color from decimal to list representation."""
    return [(color & 0xFF0000) >> 16, (color & 0x00FF00) >> 8, (color & 0x0000FF)]


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the light integration."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_light_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on its profile and attributes."""
    return (
        node.profile
        in [
            NodeProfile.DIMMABLE_LIGHT,
            NodeProfile.DIMMABLE_COLOR_LIGHT,
            NodeProfile.DIMMABLE_EXTENDED_COLOR_LIGHT,
            NodeProfile.DIMMABLE_COLOR_TEMPERATURE_LIGHT,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_AND_PRESENCE_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_PRESENCE_SENSOR,
            NodeProfile.DIMMABLE_RGBWLIGHT,
            NodeProfile.DIMMABLE_PLUG,
            NodeProfile.DIMMABLE_SWITCH,
            NodeProfile.DIMMABLE_METERING_SWITCH,
            NodeProfile.DIMMABLE_METERING_PLUG,
        ]
        and AttributeType.ON_OFF in node._attribute_map
    )


class HomeeLight(HomeeNodeEntity, LightEntity):
    """Representation of a homee light."""

    _attr_has_entity_name = True

    def __init__(
        self, node: HomeeNode, light_set, light_index, entry: ConfigEntry
    ) -> None:
        """Initialize a homee light."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_light_features(self)
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
        else:
            return f"light {self._light_index + 1}"

    @property
    def supported_features(self):
        """Return the supported features of the light."""
        return self._supported_features

    @property
    def brightness(self):
        """Return the brightness of the light."""
        # TODO: use value_to_brightness introduced in core 2023.12
        return self._dimmer_attr.current_value * 2.55

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
    def min_mireds(self):
        """Return the minimum mireds of the light."""
        return HOMEE_LIGHT_MIN_MIRED

    @property
    def max_mireds(self):
        """Return the maximum mireds of the light."""
        return HOMEE_LIGHT_MAX_MIRED

    @property
    def color_temp(self):
        """Return the color temperature of the light."""
        return color_temperature_kelvin_to_mired(
            self.get_attribute(self._temp_attr.current_value)
        )

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._on_off_attr.current_value

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        await self.async_set_value_by_id(self._on_off_attr.id, 1)

        if ATTR_BRIGHTNESS in kwargs and self._dimmer_attr is not None:
            await self.async_set_value_by_id(
                self._dimmer_attr.id,
                kwargs[ATTR_BRIGHTNESS] / 2.55,
                # TODO use percentage_to_ranged_value introduced in core 2023.12
            )
        if ATTR_COLOR_TEMP in kwargs and self._temp_attr is not None:
            await self.async_set_value_by_id(
                self._temp_attr.id,
                color_temperature_mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]),
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
