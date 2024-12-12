"""The homee switch platform."""

import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyHomee.const import AttributeType, NodeProfile
from pyHomee.model import HomeeAttribute, HomeeNode

from . import HomeeConfigEntry, HomeeNodeEntity
from .const import CLIMATE_PROFILES, LIGHT_PROFILES
from .helpers import get_imported_nodes, get_name_for_enum

_LOGGER = logging.getLogger(__name__)

HOMEE_PLUG_PROFILES = [
    NodeProfile.ON_OFF_PLUG,
    NodeProfile.METERING_PLUG,
    NodeProfile.DOUBLE_ON_OFF_PLUG,
    NodeProfile.IMPULSE_PLUG,
]

HOMEE_SWITCH_ATTRIBUTES = [
    AttributeType.AUTOMATIC_MODE_IMPULSE,
    AttributeType.BRIEFLY_OPEN_IMPULSE,
    AttributeType.EXTERNAL_BINARY_INPUT,
    AttributeType.IDENTIFICATION_MODE,
    AttributeType.IMPULSE,
    AttributeType.LIGHT_IMPULSE,
    AttributeType.MANUAL_OPERATION,
    AttributeType.MOTOR_ROTATION,
    AttributeType.OPEN_PARTIAL_IMPULSE,
    AttributeType.ON_OFF,
    AttributeType.PERMANENTLY_OPEN_IMPULSE,
    AttributeType.RESET_METER,
    AttributeType.RESTORE_LAST_KNOWN_STATE,
    AttributeType.SIREN,
    AttributeType.SWITCH_TYPE,
    AttributeType.VENTILATE_IMPULSE,
    AttributeType.WATCHDOG_ON_OFF,
]

DESCRIPTIVE_ATTRIBUTES = [
    AttributeType.AUTOMATIC_MODE_IMPULSE,
    AttributeType.BRIEFLY_OPEN_IMPULSE,
    AttributeType.EXTERNAL_BINARY_INPUT,
    AttributeType.IDENTIFICATION_MODE,
    AttributeType.LIGHT_IMPULSE,
    AttributeType.MANUAL_OPERATION,
    AttributeType.MOTOR_ROTATION,
    AttributeType.OPEN_PARTIAL_IMPULSE,
    AttributeType.PERMANENTLY_OPEN_IMPULSE,
    AttributeType.RESET_METER,
    AttributeType.RESTORE_LAST_KNOWN_STATE,
    AttributeType.SWITCH_TYPE,
    AttributeType.VENTILATE_IMPULSE,
    AttributeType.WATCHDOG_ON_OFF,
]

CONFIG_ATTRIBUTES = [
    AttributeType.EXTERNAL_BINARY_INPUT,
    AttributeType.MOTOR_ROTATION,
    AttributeType.RESET_METER,
    AttributeType.RESTORE_LAST_KNOWN_STATE,
    AttributeType.SWITCH_TYPE,
    AttributeType.WATCHDOG_ON_OFF,
]
DIAGNOSTIC_ATTRIBUTES = [AttributeType.IDENTIFICATION_MODE]


def get_device_class(node: HomeeNode) -> SwitchDeviceClass:
    """Determine the device class a homee node based on the node profile."""
    if node.profile in HOMEE_PLUG_PROFILES:
        return SwitchDeviceClass.OUTLET

    return SwitchDeviceClass.SWITCH


def get_entity_category(attribute) -> EntityCategory | None:
    """Determine the Entity Category."""
    if attribute.type in CONFIG_ATTRIBUTES:
        return EntityCategory.CONFIG

    if attribute.type in DIAGNOSTIC_ATTRIBUTES:
        return EntityCategory.DIAGNOSTIC

    return None


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HomeeConfigEntry, async_add_devices
) -> None:
    """Add the homee platform for the switch component."""

    devices = []
    for node in get_imported_nodes(config_entry):
        devices.extend(
            HomeeSwitch(node, config_entry, attribute)
            for attribute in node.attributes
            if (attribute.type in HOMEE_SWITCH_ATTRIBUTES and attribute.editable)
            and not (
                attribute.type == AttributeType.ON_OFF
                and node.profile in LIGHT_PROFILES
            )
            and not (
                attribute.type == AttributeType.MANUAL_OPERATION
                and node.profile in CLIMATE_PROFILES
            )
        )
    if devices:
        async_add_devices(devices)


class HomeeSwitch(HomeeNodeEntity, SwitchEntity):
    """Representation of a homee switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: HomeeConfigEntry,
        on_off_attribute: HomeeAttribute = None,
    ) -> None:
        """Initialize a homee switch entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._on_off = on_off_attribute
        self._switch_index = on_off_attribute.instance
        self._attr_device_class = get_device_class(node)
        self._attr_entity_category = get_entity_category(on_off_attribute)

        self._attr_unique_id = f"{self._node.id}-switch-{self._on_off.id}"

    @property
    def translation_key(self) -> str | None:
        """Return the translation key for the switch."""
        # If a switch is the main feature of a device it will get its name.
        translation_key = None

        attribute_name = get_name_for_enum(AttributeType, self._on_off.type)

        # If a switch type has more than one instance,
        # it will be named and numbered.
        if self._on_off.instance > 0:
            translation_key = f"{attribute_name.lower()}_{self._on_off.instance}"
        # Some switches should be named descriptive without an instance number.
        elif self._on_off.type in DESCRIPTIVE_ATTRIBUTES:
            translation_key = attribute_name.lower()

        if self._on_off.instance > 4:
            _LOGGER.error(
                "Did get more than 4 switches of a type,"
                "please report at"
                "https://github.com/Taraman17/hacs-homee/issues"
            )

        if translation_key is None:
            self._attr_name = None

        return translation_key

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return bool(self._on_off.current_value)

    @property
    def icon(self) -> str | None:
        """Return icon if different from main feature."""
        if self._on_off.type == AttributeType.WATCHDOG_ON_OFF:
            return "mdi:dog"
        if self._on_off.type == AttributeType.MANUAL_OPERATION:
            return "mdi:hand-back-left"

        return None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self.async_set_value_by_id(self._on_off.id, 1)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self.async_set_value_by_id(self._on_off.id, 0)

    @property
    def current_power_w(self) -> int | None:
        """Return the current power usage in W."""
        if self.has_attribute(AttributeType.CURRENT_ENERGY_USE):
            return self.attribute(AttributeType.CURRENT_ENERGY_USE)

        return None

    @property
    def today_energy_kwh(self) -> int | None:
        """Return the total power usage in kWh."""
        if self.has_attribute(AttributeType.ACCUMULATED_ENERGY_USE):
            return self.attribute(AttributeType.ACCUMULATED_ENERGY_USE)

        return None
