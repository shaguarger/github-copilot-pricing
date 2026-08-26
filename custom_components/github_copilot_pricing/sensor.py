"""Sensors for GitHub Copilot Pricing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
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
    """Set up dynamic pricing sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    manager: GitHubCopilotPricingSensorManager = data["manager"]
    manager.set_add_entities_callback(async_add_entities)


@dataclass(frozen=True)
class PriceEntityDescription:
    """Description of a dynamic price entity."""

    key: str
    field: str
    model: str
    provider: str
    tier: str | None
    threshold: str | None


class GitHubCopilotPricingSensorManager:
    """Manage dynamic pricing sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: GitHubCopilotPricingCoordinator,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._add_entities = None
        self._known: set[str] = set()
        self._unsubscribe = None

    def set_add_entities_callback(
        self, add_entities: AddEntitiesCallback
    ) -> None:
        """Connect the manager to Home Assistant's entity platform."""
        self._add_entities = add_entities

    def async_start(self) -> None:
        """Start the dynamic entity manager."""
        self._add_for_current_data()
        self._unsubscribe = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    def async_stop(self) -> None:
        """Stop the manager."""
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Add entities discovered after a refresh."""
        self._add_for_current_data()

    @callback
    def _add_for_current_data(self) -> None:
        """Create entities for new pricing fields."""
        if not self._add_entities or not self.coordinator.data:
            return

        descriptions = []
        for row_key, row in self.coordinator.data.items():
            for field in PRICE_FIELDS:
                if row.get(field) is None:
                    continue

                unique_id = self._unique_id(row_key, field)
                if unique_id in self._known:
                    continue

                descriptions.append(
                    PriceEntityDescription(
                        key=row_key,
                        field=field,
                        model=row["model"],
                        provider=row["provider"],
                        tier=row.get("tier"),
                        threshold=row.get("threshold"),
                    )
                )
                self._known.add(unique_id)

        if descriptions:
            self._add_entities(
                [
                    GitHubCopilotPriceSensor(
                        self.coordinator,
                        description,
                    )
                    for description in descriptions
                ],
                update_before_add=True,
            )

    @staticmethod
    def _unique_id(row_key: str, field: str) -> str:
        return f"{DOMAIN}_{slugify(row_key)}_{field}"


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
        self.entity_description = description

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
        row = self.coordinator.data.get(self.entity_description.key)
        if not row:
            return None
        return row.get(self.entity_description.field)

    @property
    def available(self) -> bool:
        """Return whether this pricing row still exists."""
        # Keep the last known value available during a temporary network
        # failure. Mark it unavailable only when GitHub no longer publishes
        # the pricing row.
        return self.entity_description.key in self.coordinator.data

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful source metadata."""
        row = self.coordinator.data.get(self.entity_description.key)
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
