from __future__ import annotations

import numpy as np

from scripts.analysis.context_length_compare import (
    distribution_bin_edges,
    plot_context_length_distributions,
)


def test_distribution_bin_edges_cover_all_positive_counts():
    edges = distribution_bin_edges(
        [
            ("first", np.array([50, 100, 1_000])),
            ("second", np.array([10_000, 100_000])),
        ],
        5,
    )

    assert len(edges) == 5
    assert edges[0] == 100
    assert edges[-1] == 100_000
    assert np.all(np.diff(edges) > 0)


def test_plot_context_length_distributions_writes_png(tmp_path):
    output_path = tmp_path / "distribution.png"

    plot_context_length_distributions(
        [("dataset", np.array([100, 1_000, 10_000]))],
        output_path,
        bin_count=5,
        title="Test distribution",
    )

    assert output_path.is_file()
    assert output_path.stat().st_size > 0
