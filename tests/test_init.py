from unittest.mock import patch

from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.github_copilot_pricing.const import DOMAIN


async def test_setup_creates_sensors(hass):
    entry = MockConfigEntry(domain=DOMAIN, options={"scan_interval": 6})
    entry.add_to_hass(hass)
    pricing = {
        "openai|Example|Default|not_applicable": {
            "model": "Example",
            "provider": "openai",
            "release_status": "GA",
            "category": "Test",
            "tier": "Default",
            "threshold": None,
            "notes": None,
            "input": 1.0,
            "cached_input": None,
            "cache_write": None,
            "output": 2.0,
        }
    }

    with patch(
        "custom_components.github_copilot_pricing.coordinator."
        "GitHubCopilotPricingCoordinator._async_update_data",
        return_value=pricing,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    states = hass.states.async_all("sensor")
    assert {state.state for state in states} == {"1.0", "2.0"}
    assert all(state.attributes["provider"] == "openai" for state in states)
    devices = dr.async_get(hass).devices.values()
    assert [(device.name, device.manufacturer) for device in devices] == [
        ("Example", "Openai")
    ]
    assert "github-copilot-pricing" in hass.data["frontend_panels"]

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert "github-copilot-pricing" not in hass.data["frontend_panels"]
    with patch(
        "custom_components.github_copilot_pricing.coordinator."
        "GitHubCopilotPricingCoordinator._async_update_data",
        return_value=pricing,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
