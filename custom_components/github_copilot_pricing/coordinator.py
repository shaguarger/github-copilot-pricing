"""Data coordinator for GitHub Copilot Pricing."""
from __future__ import annotations

from datetime import timedelta
import logging
import re
from typing import Any

import aiohttp
import yaml

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    PRICING_URL,
)

_LOGGER = logging.getLogger(__name__)


def parse_price(value: Any) -> float | None:
    """Convert a GitHub price value such as '$1.25' to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text.lower() in {
        "not applicable",
        "n/a",
        "na",
        "none",
        "-",
    }:
        return None

    text = text.replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def slugify(value: str) -> str:
    """Create a stable Home Assistant entity-id fragment."""
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def pricing_key(item: dict[str, Any]) -> str:
    """Create a stable key for one pricing row."""
    parts = (
        item.get("provider") or "unknown",
        item.get("model") or "unknown",
        item.get("tier") or "default",
        item.get("threshold") or "not_applicable",
    )
    return "|".join(str(part) for part in parts)


def normalize_pricing(raw: Any) -> dict[str, dict[str, Any]]:
    """Normalize GitHub's pricing YAML into stable keyed rows."""
    if not isinstance(raw, list):
        raise ValueError("Expected the pricing YAML root to be a list")

    result: dict[str, dict[str, Any]] = {}

    for row in raw:
        if not isinstance(row, dict):
            continue

        model = row.get("model")
        provider = row.get("provider")
        if not model or not provider:
            continue

        item = {
            "model": str(model),
            "provider": str(provider),
            "release_status": row.get("release_status"),
            "category": row.get("category"),
            "tier": row.get("tier"),
            "threshold": row.get("threshold"),
            "notes": row.get("notes"),
            "input": parse_price(row.get("input")),
            "cached_input": parse_price(row.get("cached_input")),
            "cache_write": parse_price(row.get("cache_write")),
            "output": parse_price(row.get("output")),
        }

        key = pricing_key(item)
        result[key] = item

    if not result:
        raise ValueError("No valid pricing rows found")

    return result


class GitHubCopilotPricingCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, Any]]]
):
    """Fetch and normalize GitHub Copilot pricing."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        hours = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
        )
        super().__init__(
            hass,
            _LOGGER,
            name="GitHub Copilot Pricing",
            update_interval=timedelta(hours=hours),
        )
        self.last_successful_update = None
        self.previous_data: dict[str, dict[str, Any]] = {}
        self.price_changes: list[dict[str, Any]] = []

    def _record_changes(self, new_data: dict[str, dict[str, Any]]) -> None:
        """Detect price changes and expose them as a Home Assistant event."""
        if not self.previous_data:
            self.previous_data = new_data
            self.price_changes = []
            return

        changes: list[dict[str, Any]] = []

        for key, new_row in new_data.items():
            old_row = self.previous_data.get(key)

            if old_row is None:
                changes.append(
                    {
                        "type": "added",
                        "model": new_row["model"],
                        "provider": new_row["provider"],
                        "tier": new_row.get("tier"),
                    }
                )
                continue

            for field in ("input", "cached_input", "cache_write", "output"):
                old_price = old_row.get(field)
                new_price = new_row.get(field)

                if old_price != new_price:
                    changes.append(
                        {
                            "type": "price_changed",
                            "model": new_row["model"],
                            "provider": new_row["provider"],
                            "tier": new_row.get("tier"),
                            "field": field,
                            "old": old_price,
                            "new": new_price,
                        }
                    )

        for key, old_row in self.previous_data.items():
            if key not in new_data:
                changes.append(
                    {
                        "type": "removed",
                        "model": old_row["model"],
                        "provider": old_row["provider"],
                        "tier": old_row.get("tier"),
                    }
                )

        self.price_changes = changes

        if changes:
            self.hass.bus.async_fire(
                "github_copilot_pricing_changed",
                {
                    "changes": changes,
                    "model_count": len(new_data),
                    "source": PRICING_URL,
                },
            )

            _LOGGER.info(
                "Detected %d GitHub Copilot pricing changes",
                len(changes),
            )

        self.previous_data = new_data


    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch the current pricing."""
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    PRICING_URL,
                    headers={
                        "Accept": "text/plain",
                        "User-Agent": "Home Assistant GitHub Copilot Pricing",
                    },
                ) as response:
                    response.raise_for_status()
                    content = await response.text()

            raw = yaml.safe_load(content)
            data = normalize_pricing(raw)
            self._record_changes(data)
            self.last_successful_update = self.hass.loop.time()

            _LOGGER.debug(
                "Loaded %d GitHub Copilot pricing rows", len(data)
            )
            return data

        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(
                f"Unable to download GitHub Copilot pricing: {err}"
            ) from err
        except yaml.YAMLError as err:
            raise UpdateFailed(
                f"Unable to parse GitHub Copilot pricing YAML: {err}"
            ) from err
        except ValueError as err:
            raise UpdateFailed(str(err)) from err
