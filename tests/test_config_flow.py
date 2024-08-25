"""Test the Homee config flow."""

from unittest.mock import MagicMock, patch, ANY

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homee import config_flow
from custom_components.homee.const import (
    CONF_ADD_HOMEE_DATA,
    CONF_ALL_DEVICES,
    CONF_DOOR_GROUPS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
)
from pymee import AuthenticationFailedException

from .conftest import (
    HOMEE_ID,
    HOMEE_IP,
    SCHEMA_IMPORT_ALL,
    SCHEMA_IMPORT_GROUPS,
    TESTPASS,
    TESTUSER,
)


async def test_flow(hass: HomeAssistant, mock_homee: MagicMock) -> None:
    """Test the complete config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expected = {
        "data_schema": config_flow.AUTH_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": ANY,
        "handler": DOMAIN,
        "step_id": "user",
        "type": FlowResultType.FORM,
        "last_step": None,
        "preview": None,
    }
    assert result == expected

    flow_id = result["flow_id"]

    groups_result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
            CONF_ALL_DEVICES: "all",
            CONF_ADD_HOMEE_DATA: False,
        },
    )

    assert groups_result["type"] == FlowResultType.FORM
    assert groups_result["step_id"] == "groups"
    # we can't directly compare the schemas, since the objects differ if manually built here.
    assert (
        groups_result["data_schema"].schema.items.__sizeof__()
        == SCHEMA_IMPORT_ALL.schema.items.__sizeof__()
    )

    final_result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={CONF_DOOR_GROUPS: [], CONF_WINDOW_GROUPS: []},
    )

    expected = {
        "type": FlowResultType.CREATE_ENTRY,
        "flow_id": flow_id,
        "handler": DOMAIN,
        "data": {"host": HOMEE_IP, "username": TESTUSER, "password": TESTPASS},
        "description": None,
        "description_placeholders": None,
        "context": {"source": "user", "unique_id": HOMEE_ID},
        "title": f"{HOMEE_ID} ({HOMEE_IP})",
        "minor_version": 1,
        "options": {
            "all_devices_or_groups": True,
            "add_homee_data": False,
            "groups": {"door_groups": [], "window_groups": []},
        },
        "version": 2,
        "result": ANY,
    }

    assert expected == final_result

async def test_flow_only_groups(hass: HomeAssistant, mock_homee: MagicMock) -> None:
    """Test the Config Flow with "only groups" option."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]

    groups_result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
            CONF_ALL_DEVICES: "groups",
            CONF_ADD_HOMEE_DATA: False,
        },
    )

    assert groups_result["type"] == FlowResultType.FORM
    assert groups_result["step_id"] == "groups"
    # we can't directly compare the schemas, since the objects differ if manually built here.
    assert (
        groups_result["data_schema"].schema.items.__sizeof__()
        == SCHEMA_IMPORT_GROUPS.schema.items.__sizeof__()
    )

async def test_flow_already_configured(
    hass: HomeAssistant,
    mock_homee: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test config flow aborts when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
            CONF_ALL_DEVICES: "all",
            CONF_ADD_HOMEE_DATA: False,
        },
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
