from custom_components.github_copilot_pricing.coordinator import (
    normalize_pricing,
    parse_price,
    pricing_key,
    slugify,
)


def test_parse_price():
    assert parse_price("$1.25") == 1.25
    assert parse_price("$0.025") == 0.025
    assert parse_price("Not applicable") is None
    assert parse_price(None) is None


def test_slugify():
    assert slugify("GPT-5.6 Luna") == "gpt_5_6_luna"
    assert slugify("Long context") == "long_context"


def test_pricing_key():
    row = {
        "provider": "openai",
        "model": "GPT-5.6 Luna",
        "tier": "Default",
        "threshold": "≤ 200K",
    }
    assert pricing_key(row) == (
        "openai|GPT-5.6 Luna|Default|≤ 200K"
    )


def test_normalize_pricing():
    raw = [
        {
            "model": "GPT-5.6 Luna",
            "provider": "openai",
            "release_status": "GA",
            "category": "Lightweight",
            "threshold": "≤ 200K",
            "tier": "Default",
            "input": "$0.20",
            "cached_input": "$0.02",
            "cache_write": "$0.25",
            "output": "$1.20",
        },
        {
            "model": "Example",
            "provider": "test",
            "input": "Not applicable",
            "output": "$2.00",
        },
    ]

    data = normalize_pricing(raw)

    assert len(data) == 2
    luna = next(v for v in data.values() if v["model"] == "GPT-5.6 Luna")
    assert luna["input"] == 0.20
    assert luna["cached_input"] == 0.02
    assert luna["cache_write"] == 0.25
    assert luna["output"] == 1.20


def test_long_context_rows_have_distinct_keys():
    base = {
        "provider": "openai",
        "model": "GPT-5.6 Luna",
        "threshold": "≤ 200K",
        "tier": "Default",
    }
    long_context = {
        **base,
        "threshold": "> 200K",
        "tier": "Long context",
    }
    assert pricing_key(base) != pricing_key(long_context)


def test_current_github_pricing_schema():
    """Keep GitHub's current source shape covered without network access."""
    raw = [
        {
            "model": "Example",
            "provider": "openai",
            "tier": "Default",
            "threshold": "Not applicable",
            "input": "$1.00",
            "cached_input": "$0.10",
            "cache_write": "Not applicable",
            "output": "$2.00",
        }
    ]
    assert len(normalize_pricing(raw)) == 1
