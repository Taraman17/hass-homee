"""Fixtures for Homee integration tests."""

from unittest.mock import MagicMock, patch

from pymee.model import HomeeGroup
import pytest
from typing_extensions import Generator
import voluptuous as vol

from pytest_homeassistant_custom_component.common import (
    load_json_object_fixture,
    MockConfigEntry,
)

from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from custom_components.homee.const import (
    CONF_DOOR_GROUPS,
    CONF_IMPORT_GROUPS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
)

HOMEE_ID = "00055511EECC"
HOMEE_IP = "192.168.1.11"
TESTUSER = "testuser"
TESTPASS = "testpass"

GROUPS_SELECTION = {'1': 'Group1 (0)', '3': 'Group2 (0)'}

SCHEMA_IMPORT_GROUPS = vol.Schema(
    {
        vol.Required(
            CONF_IMPORT_GROUPS,
            default=['1', '3'],
        ): cv.multi_select(GROUPS_SELECTION),
        vol.Required(
            CONF_WINDOW_GROUPS,
            default=[],
        ): cv.multi_select(GROUPS_SELECTION),
        vol.Required(
            CONF_DOOR_GROUPS,
            default=[],
        ): cv.multi_select(GROUPS_SELECTION),
    }
)

SCHEMA_IMPORT_ALL = vol.Schema(
    {
        vol.Required(
            CONF_WINDOW_GROUPS,
            default=[],
        ): cv.multi_select(GROUPS_SELECTION),
        vol.Required(
            CONF_DOOR_GROUPS,
            default=[],
        ): cv.multi_select(GROUPS_SELECTION),
    }
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title=f"{HOMEE_ID} ({HOMEE_IP})",
        domain=DOMAIN,
        data={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
        unique_id=HOMEE_ID,
        version=2,
        minor_version=1,
    )


@pytest.fixture
def mock_homee() -> Generator[MagicMock]:
    """Return a mock Homee instance."""
    with patch(
        "custom_components.homee.config_flow.validate_and_connect"
    ) as mocked_homee:
        homee = mocked_homee.return_value

        homee.host = HOMEE_IP
        homee.user = TESTUSER
        homee.password = TESTPASS
        homee.settings.uid = HOMEE_ID
        homee.reconnect_interval = 10

        homee.get_access_token.return_value = "test_token"
        homee.wait_until_connected.return_value = True
        homee.wait_until_disconnected.return_value = True

        homee.groups = []
        homee.groups.append(HomeeGroup(load_json_object_fixture("group1.json")))
        homee.groups.append(HomeeGroup(load_json_object_fixture("group2.json")))

        yield homee
