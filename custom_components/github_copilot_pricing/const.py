"""Constants for GitHub Copilot Pricing."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "github_copilot_pricing"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_HOURS = 6
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 168

PRICING_URL = (
    "https://raw.githubusercontent.com/github/docs/main/"
    "data/tables/copilot/models-and-pricing.yml"
)

GITHUB_DOCS_URL = (
    "https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing"
)
SOURCE_URL = (
    "https://github.com/github/docs/blob/main/"
    "data/tables/copilot/models-and-pricing.yml"
)

ATTR_MODEL = "model"
ATTR_PROVIDER = "provider"
ATTR_RELEASE_STATUS = "release_status"
ATTR_CATEGORY = "category"
ATTR_TIER = "tier"
ATTR_THRESHOLD = "threshold"
ATTR_NOTES = "notes"
ATTR_PRICE_UNIT = "price_unit"
ATTR_SOURCE = "source"
ATTR_SOURCE_URL = "source_url"
ATTR_LAST_UPDATED = "last_updated"

PRICE_FIELDS = (
    "input",
    "cached_input",
    "cache_write",
    "output",
)

PRICE_NAMES = {
    "input": "Input",
    "cached_input": "Cached input",
    "cache_write": "Cache write",
    "output": "Output",
}

UPDATE_INTERVAL = timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS)
