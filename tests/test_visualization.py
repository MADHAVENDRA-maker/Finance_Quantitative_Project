import matplotlib
import pandas as pd
import pytest

from project_structure.features.visualization import (
    plot_correlation_heatmap,
    plot_rolling_correlation,
)


@pytest.fixture
def sample_returns() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "SPY": [0.01, 0.02, -0.01, 0.03, -0.02,
                    0.01, 0.015, -0.005, 0.02, -0.01],
            "TLT": [-0.005, 0.01, 0.02, -0.01, 0.005,
                    0.01, -0.015, 0.02, -0.005, 0.01],
        },
        index=index,
    )


def test_heatmap_creates_image_file(tmp_path) -> None:
    correlation = pd.DataFrame(
        [[1.0, 0.4], [0.4, 1.0]],
        index=["SPY", "TLT"],
        columns=["SPY", "TLT"],
    )
    output = tmp_path / "charts" / "correlation.png"

    result = plot_correlation_heatmap(correlation, output)

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_heatmap_rejects_non_square_matrix(tmp_path) -> None:
    correlation = pd.DataFrame([[1.0, 0.5]], columns=["SPY", "TLT"])

    with pytest.raises(ValueError, match="square"):
        plot_correlation_heatmap(correlation, tmp_path / "bad.png")


def test_heatmap_rejects_out_of_range_values(tmp_path) -> None:
    correlation = pd.DataFrame(
        [[1.0, 1.5], [1.5, 1.0]],
        index=["SPY", "TLT"],
        columns=["SPY", "TLT"],
    )

    with pytest.raises(ValueError, match="between -1 and 1"):
        plot_correlation_heatmap(correlation, tmp_path / "bad.png")


def test_rolling_correlation_creates_image_file(
    sample_returns: pd.DataFrame,
    tmp_path,
) -> None:
    output = tmp_path / "rolling.png"

    result = plot_rolling_correlation(
        sample_returns,
        "SPY",
        "TLT",
        output,
        window=3,
    )

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_rolling_plot_rejects_unknown_asset(
    sample_returns: pd.DataFrame,
    tmp_path,
) -> None:
    with pytest.raises(ValueError, match="Both assets"):
        plot_rolling_correlation(
            sample_returns,
            "SPY",
            "UNKNOWN",
            tmp_path / "bad.png",
            window=3,
        )


def test_visualization_uses_non_interactive_backend() -> None:
    assert matplotlib.get_backend().lower() == "agg"