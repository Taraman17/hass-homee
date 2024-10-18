"""Constants for the homee integration."""

from pymee.const import NodeProfile

# General
DOMAIN = "homee"

# Services
SERVICE_SET_VALUE = "set_value"
SERVICE_UPDATE_ENTITY = "update_entity"

# Attributes
ATTR_ATTRIBUTE = "attribute"
ATTR_HOMEE_DATA = "homee_data"
ATTR_NODE = "node"
ATTR_VALUE = "value"

# Profile Groups
CLIMATE_PROFILES = [
    NodeProfile.COSI_THERM_CHANNEL,
    NodeProfile.HEATING_SYSTEM,
    NodeProfile.RADIATOR_THERMOSTAT,
    NodeProfile.ROOM_THERMOSTAT,
    NodeProfile.ROOM_THERMOSTAT_WITH_HUMIDITY_SENSOR,
    NodeProfile.THERMOSTAT_WITH_HEATING_AND_COOLING,
    NodeProfile.WIFI_RADIATOR_THERMOSTAT,
    NodeProfile.WIFI_ROOM_THERMOSTAT,
]
LIGHT_PROFILES = [
    NodeProfile.DIMMABLE_COLOR_LIGHT,
    NodeProfile.DIMMABLE_COLOR_METERING_PLUG,
    NodeProfile.DIMMABLE_COLOR_TEMPERATURE_LIGHT,
    NodeProfile.DIMMABLE_EXTENDED_COLOR_LIGHT,
    NodeProfile.DIMMABLE_LIGHT,
    NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_SENSOR,
    NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_AND_PRESENCE_SENSOR,
    NodeProfile.DIMMABLE_LIGHT_WITH_PRESENCE_SENSOR,
    NodeProfile.DIMMABLE_METERING_SWITCH,
    NodeProfile.DIMMABLE_METERING_PLUG,
    NodeProfile.DIMMABLE_PLUG,
    NodeProfile.DIMMABLE_RGBWLIGHT,
    NodeProfile.DIMMABLE_SWITCH,
    NodeProfile.WIFI_DIMMABLE_RGBWLIGHT,
    NodeProfile.WIFI_DIMMABLE_LIGHT,
    NodeProfile.WIFI_ON_OFF_DIMMABLE_METERING_SWITCH,
]

HOMEE_LIGHT_MIN_MIRED = 153
HOMEE_LIGHT_MAX_MIRED = 556

# Options
CONF_INITIAL_OPTIONS = "initial_options"
CONF_ALL_DEVICES = "all_devices_or_groups"
CONF_ADD_HOMEE_DATA = "add_homee_data"
CONF_GROUPS = "groups"
CONF_IMPORT_GROUPS = "import_groups"
CONF_WINDOW_GROUPS = "window_groups"
CONF_DOOR_GROUPS = "door_groups"

# Climate Presets
PRESET_MANUAL = "manual"
