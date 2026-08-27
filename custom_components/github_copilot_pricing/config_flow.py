"""Config flow for GitHub Copilot Pricing."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import AreaSelector

from .const import (
    CONF_AREA_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
)


class GitHubCopilotPricingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup."""
        if user_input is not None:
            return self.async_create_entry(
                title="GitHub Copilot Pricing",
                data={},
                options=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL_HOURS,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_HOURS,
                            max=MAX_SCAN_INTERVAL_HOURS,
                        ),
                    ),
                    vol.Optional(CONF_AREA_ID): AreaSelector(),
                }
            ),
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return GitHubCopilotPricingOptionsFlow()


class GitHubCopilotPricingOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
        )
        area_id = self.config_entry.options.get(CONF_AREA_ID)
        area = (
            vol.Optional(CONF_AREA_ID, default=area_id)
            if area_id
            else vol.Optional(CONF_AREA_ID)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_HOURS,
                            max=MAX_SCAN_INTERVAL_HOURS,
                        ),
                    ),
                    area: AreaSelector(),
                }
            ),
        )
