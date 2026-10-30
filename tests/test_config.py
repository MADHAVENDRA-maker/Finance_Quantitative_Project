from pathlib import Path

import pytest
from pydantic import ValidationError

from project_structure.config import AssetConfig, AssetsConfig, load_assets_config


def test_load_default_assets_config() -> None:
    config = load_assets_config()

    assert len(config.assets) == 10
    assert config.assets[0].ticker == "SPY"
    assert len({asset.ticker for asset in config.assets}) == 10


def test_ticker_is_normalized_to_uppercase() -> None:
    asset = AssetConfig(
        ticker="spy",
        name="Test ETF",
        asset_class="Equity",
        description="Test asset.",
    )

    assert asset.ticker == "SPY"


def test_duplicate_tickers_are_rejected() -> None:
    asset = {
        "ticker": "SPY",
        "name": "Test ETF",
        "asset_class": "Equity",
        "description": "Test asset.",
    }

    with pytest.raises(ValidationError, match="unique"):
        AssetsConfig.model_validate({"assets": [asset, asset]})


def test_empty_required_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AssetConfig(
            ticker="SPY",
            name="",
            asset_class="Equity",
            description="Test asset.",
        )


def test_unexpected_asset_field_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AssetConfig(
            ticker="SPY",
            name="Test ETF",
            asset_class="Equity",
            description="Test asset.",
            unexpected_field="not allowed",
        )


def test_missing_config_file_raises_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_assets.yaml"

    with pytest.raises(FileNotFoundError, match="not found"):
        load_assets_config(missing_path)