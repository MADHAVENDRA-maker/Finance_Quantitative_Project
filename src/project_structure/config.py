from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS_CONFIG = PROJECT_ROOT / "configs" / "assets.yaml"


class AssetConfig(BaseModel):
    """Configuration for a single investable asset."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    asset_class: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.upper()


class AssetsConfig(BaseModel):
    """Validated collection of configured assets."""

    model_config = ConfigDict(extra="forbid")

    assets: list[AssetConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_tickers(self) -> "AssetsConfig":
        tickers = [asset.ticker for asset in self.assets]
        if len(tickers) != len(set(tickers)):
            raise ValueError("Asset tickers must be unique.")
        return self


def load_assets_config(
    config_path: str | Path = DEFAULT_ASSETS_CONFIG,
) -> AssetsConfig:
    """Load and validate the asset universe from a YAML file."""

    path = Path(config_path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.is_file():
        raise FileNotFoundError(f"Asset configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if not isinstance(raw_config, dict):
        raise ValueError("Asset configuration must be a YAML mapping.")

    return AssetsConfig.model_validate(raw_config)