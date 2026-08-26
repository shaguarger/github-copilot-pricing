"""GitHub Copilot Pricing integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GitHubCopilotPricingCoordinator
from .sensor import GitHubCopilotPricingSensorManager


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up GitHub Copilot Pricing from a config entry."""
    coordinator = GitHubCopilotPricingCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    manager = GitHubCopilotPricingSensorManager(
        hass, entry, coordinator
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "manager": manager,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor"]
    )

    manager.async_start()
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id)
    data["manager"].async_stop()

    return await hass.config_entries.async_unload_platforms(
        entry, ["sensor"]
    )
