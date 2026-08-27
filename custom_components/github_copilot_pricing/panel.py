"""Frontend panel for GitHub Copilot Pricing."""
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

PANEL_PATH = "github-copilot-pricing"
PANEL_URL = "/github_copilot_pricing/panel.js"
PANEL_STATIC_REGISTERED = "github_copilot_pricing_panel_static_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the pricing overview panel once."""
    if PANEL_PATH in hass.data.get("frontend_panels", {}):
        return

    if not hass.data.get(PANEL_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_URL,
                    str(Path(__file__).with_name("panel.js")),
                    cache_headers=False,
                )
            ]
        )
        hass.data[PANEL_STATIC_REGISTERED] = True
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_PATH,
        webcomponent_name="github-copilot-pricing-panel",
        module_url=PANEL_URL,
        sidebar_title="Copilot Pricing",
        sidebar_icon="mdi:chart-line",
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the pricing panel."""
    frontend.async_remove_panel(hass, PANEL_PATH)
