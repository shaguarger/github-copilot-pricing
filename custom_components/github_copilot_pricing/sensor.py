"""Sensors for GitHub Copilot Pricing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CATEGORY,
    ATTR_MODEL,
    ATTR_NOTES,
    ATTR_PRICE_UNIT,
    ATTR_PROVIDER,
    ATTR_RELEASE_STATUS,
    ATTR_SOURCE,
    ATTR_SOURCE_URL,
    ATTR_THRESHOLD,
    ATTR_TIER,
    DOMAIN,
    GITHUB_DOCS_URL,
    PRICE_FIELDS,
    PRICE_NAMES,
    SOURCE_URL,
)
from .coordinator import (
    GitHubCopilotPricingCoordinator,
    slugify,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up pricing sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    def add_new_entities() -> None:
        descriptions = [
            PriceEntityDescription(
                key=row_key,
                field=field,
                model=row["model"],
                provider=row["provider"],
                tier=row.get("tier"),
                threshold=row.get("threshold"),
            )
            for row_key, row in coordinator.data.items()
            for field in PRICE_FIELDS
            if row.get(field) is not None
            and f"{row_key}|{field}" not in known
        ]
        known.update(
            f"{description.key}|{description.field}"
            for description in descriptions
        )
        async_add_entities(
            GitHubCopilotPriceSensor(coordinator, description)
            for description in descriptions
        )

    add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_new_entities))


@dataclass(frozen=True)
class PriceEntityDescription:
    """Description of a dynamic price entity."""

    key: str
    field: str
    model: str
    provider: str
    tier: str | None
    threshold: str | None


class GitHubCopilotPriceSensor(
    CoordinatorEntity[GitHubCopilotPricingCoordinator],
    SensorEntity,
):
    """One dynamic sensor for one model/tier/price field."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_suggested_display_precision = 4

    def __init__(
        self,
        coordinator: GitHubCopilotPricingCoordinator,
        description: PriceEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.description = description

        tier = description.tier
        tier_suffix = f" — {tier}" if tier and tier != "Default" else ""

        self._attr_name = (
            f"{description.model}{tier_suffix} — "
            f"{PRICE_NAMES[description.field]}"
        )

        self._attr_unique_id = (
            f"{DOMAIN}_{slugify(description.key)}_{description.field}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "github")},
            name="GitHub Copilot Pricing",
            manufacturer="GitHub",
            model="Copilot model pricing",
            configuration_url=GITHUB_DOCS_URL,
        )

        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        row = self.coordinator.data.get(self.description.key)
        if not row:
            return None
        return row.get(self.description.field)

    @property
    def available(self) -> bool:
        """Return whether this pricing row still exists."""
        # Keep the last known value available during a temporary network
        # failure. Mark it unavailable only when GitHub no longer publishes
        # the pricing row.
        return self.description.key in self.coordinator.data

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful source metadata."""
        row = self.coordinator.data.get(self.description.key)
        if not row:
            return {}

        return {
            ATTR_MODEL: row.get("model"),
            ATTR_PROVIDER: row.get("provider"),
            ATTR_RELEASE_STATUS: row.get("release_status"),
            ATTR_CATEGORY: row.get("category"),
            ATTR_TIER: row.get("tier"),
            ATTR_THRESHOLD: row.get("threshold"),
            ATTR_NOTES: row.get("notes"),
            ATTR_PRICE_UNIT: "USD per 1 million tokens",
            ATTR_SOURCE: "GitHub Copilot",
            ATTR_SOURCE_URL: SOURCE_URL,
        }
