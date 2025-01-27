"""The Homee select platform."""

from pyHomee.const import AttributeType
from pyHomee.model import HomeeAttribute

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeeConfigEntry
from .entity import HomeeEntity

SELECT_DESCRIPTIONS: dict[AttributeType, SelectEntityDescription] = {
    AttributeType.REPEATER_MODE: SelectEntityDescription(
        key="repeater_mode",
        options=["off", "level1", "level2"],
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomeeConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Add the homee platform for the cover integration."""

    devices: list[HomeeSelect] = []
    for node in config_entry.runtime_data.nodes:
        devices.extend(
            HomeeSelect(attribute, config_entry, SELECT_DESCRIPTIONS[attribute.type])
            for attribute in node.attributes
            if attribute.type in SELECT_DESCRIPTIONS and not attribute.editable
        )
    if devices:
        async_add_devices(devices)

class HomeeSelect(HomeeEntity, SelectEntity):
    """Representation of a homee select device."""

    def __init__(
        self,
        attribute: HomeeAttribute,
        entry: HomeeConfigEntry,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize a homee sensor entity."""
        super().__init__(attribute, entry)
        self.entity_description = description
        if description.options:
            self._attr_options = description.options
        self._attr_translation_key = description.key

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return self.options[int(self._attribute.current_value)]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.async_set_value(self.options.index(option))
