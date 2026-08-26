# GitHub Copilot Pricing for Home Assistant

A Home Assistant custom integration that tracks the model pricing published by GitHub for GitHub Copilot.

It reads GitHub's structured pricing source:

`github/docs/data/tables/copilot/models-and-pricing.yml`

The integration does **not** scrape the rendered documentation page.

## Features

- UI-based Home Assistant setup
- No GitHub token required
- Official GitHub pricing source
- Configurable refresh interval: 1–168 hours
- Dynamically creates sensors for new pricing rows and price fields
- Handles model pricing tiers such as Default / Long context
- Keeps stable entity IDs when GitHub changes prices
- Exposes provider, model, category, release status, tier and threshold as attributes
- Uses a Home Assistant `DataUpdateCoordinator`
- No MQTT dependency
- No external Python service
- Price values are USD per 1 million tokens

## Installation

### HACS

1. Open HACS.
2. Add this repository as a custom repository.
3. Select **Integration**.
4. Install **GitHub Copilot Pricing**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **GitHub Copilot Pricing**.

### Manual

Copy:

```text
custom_components/github_copilot_pricing
```

to:

```text
/config/custom_components/github_copilot_pricing
```

Restart Home Assistant and add the integration through the UI.

## Entities

One sensor is created for each model pricing row and available price field.

Examples:

```text
sensor.github_copilot_pricing_gpt_5_6_luna_default_input
sensor.github_copilot_pricing_gpt_5_6_luna_default_cached_input
sensor.github_copilot_pricing_gpt_5_6_luna_default_cache_write
sensor.github_copilot_pricing_gpt_5_6_luna_default_output
```

Long-context pricing is represented separately.

The exact entity IDs depend on the model/provider/tier data published by GitHub.

## Dynamic updates

The integration checks the source periodically.

If GitHub adds a new model or pricing tier, new entities are added without reinstalling the integration.

If a pricing row disappears, its entity remains in Home Assistant but becomes unavailable. This deliberately avoids deleting historical entity registry entries and their statistics.

If GitHub changes a price, the existing entity keeps its identity and simply reports the new value.

The integration also fires the Home Assistant event `github_copilot_pricing_changed`
when models are added/removed or a published price changes. The event contains a
`changes` array with the old and new values where applicable.

## Data source

GitHub publishes the structured pricing data in:

https://github.com/github/docs/blob/main/data/tables/copilot/models-and-pricing.yml

The user-facing documentation is:

https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing

GitHub states that prices are per 1 million tokens.

## Development

Create a virtual environment and install test dependencies:

```bash
python -m pip install -r requirements_test.txt
```

Run tests:

```bash
pytest
```

## License

MIT
