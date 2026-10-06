from __future__ import annotations

import pytest

from cerberus.retrieval import cosine_distance, rank_dense, rank_sparse, tokenize


@pytest.fixture
def records() -> list[dict[str, object]]:
    return [
        {
            "video_id": "delivery",
            "pathname": "delivery.mp4",
            "description": "Package package delivery at the door",
            "embedding": [1.0, 0.0],
            "query": "stale input metadata",
            "rank": 99,
        },
        {
            "video_id": "animal",
            "pathname": "animal.mp4",
            "description": "A dog crosses the driveway",
            "embedding": [0.0, 1.0],
        },
        {
            "video_id": "porch",
            "pathname": "porch.mp4",
            "description": "A package is left on the front porch",
            "embedding": [0.8, 0.2],
        },
    ]


def test_tokenize_is_case_insensitive_and_keeps_apostrophes() -> None:
    assert tokenize("DON'T Stop, Package-Delivery!") == [
        "don't",
        "stop",
        "package",
        "delivery",
    ]


def test_sparse_ranking_is_relevant_ranked_and_overwrites_stale_metadata(
    records: list[dict[str, object]],
) -> None:
    results = rank_sparse(records, "PACKAGE delivery", 5)

    assert [record["video_id"] for record in results] == ["delivery", "porch"]
    assert [record["rank"] for record in results] == [1, 2]
    assert all(record["query"] == "PACKAGE delivery" for record in results)
    assert all(record["retrieval_method"] == "sparse" for record in results)
    assert results[0]["score"] > results[1]["score"] > 0


def test_sparse_ranking_returns_no_results_for_empty_query_or_corpus(
    records: list[dict[str, object]],
) -> None:
    assert rank_sparse(records, "   ", 2) == []
    assert rank_sparse([], "package", 2) == []


def test_sparse_ranking_validates_k_and_descriptions(
    records: list[dict[str, object]],
) -> None:
    with pytest.raises(ValueError, match="k must be at least 1"):
        rank_sparse(records, "package", 0)
    with pytest.raises(ValueError, match="record 0 has no non-empty description"):
        rank_sparse([{"description": None}], "package", 1)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"k1": 0}, "k1 must be positive"),
        ({"b": -0.1}, "b must be between 0 and 1"),
        ({"b": 1.1}, "b must be between 0 and 1"),
    ],
)
def test_sparse_ranking_validates_bm25_parameters(
    records: list[dict[str, object]], kwargs: dict[str, float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        rank_sparse(records, "package", 1, **kwargs)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([1.0, 0.0], [1.0, 0.0], 0.0),
        ([1.0, 0.0], [0.0, 1.0], 1.0),
        ([1.0, 0.0], [-1.0, 0.0], 2.0),
    ],
)
def test_cosine_distance_known_vectors(
    left: list[float], right: list[float], expected: float
) -> None:
    assert cosine_distance(left, right) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("left", "right", "message"),
    [
        ([], [1.0], "vectors cannot be empty"),
        ([1.0], [1.0, 2.0], "vector dimensions differ"),
        ([0.0, 0.0], [1.0, 0.0], "undefined for zero vectors"),
    ],
)
def test_cosine_distance_validates_vectors(
    left: list[float], right: list[float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        cosine_distance(left, right)


def test_dense_ranking_uses_cosine_distance_and_stable_result_metadata(
    records: list[dict[str, object]],
) -> None:
    results = rank_dense(records, "find delivery", [1.0, 0.0], 10)

    assert [record["video_id"] for record in results] == [
        "delivery",
        "porch",
        "animal",
    ]
    assert [record["rank"] for record in results] == [1, 2, 3]
    assert results[0]["query"] == "find delivery"
    assert results[0]["distance"] == pytest.approx(0.0)
    assert all(record["retrieval_method"] == "dense" for record in results)


def test_dense_ranking_breaks_equal_distance_ties_by_input_order() -> None:
    records = [
        {"video_id": "first", "embedding": [1.0, 0.0]},
        {"video_id": "second", "embedding": [1.0, 0.0]},
    ]

    assert [item["video_id"] for item in rank_dense(records, "query", [1, 0], 2)] == [
        "first",
        "second",
    ]


def test_dense_ranking_validates_query_k_and_record_embeddings(
    records: list[dict[str, object]],
) -> None:
    with pytest.raises(ValueError, match="k must be at least 1"):
        rank_dense(records, "query", [1, 0], 0)
    with pytest.raises(ValueError, match="query cannot be empty"):
        rank_dense(records, " ", [1, 0], 1)
    with pytest.raises(ValueError, match="record 0 has no embedding list"):
        rank_dense([{"embedding": (1.0, 0.0)}], "query", [1, 0], 1)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("side", ["left", "right"])
def test_cosine_rejects_nonfinite_input(value: float, side: str) -> None:
    left, right = [1.0, 0.0], [1.0, 0.0]
    (left if side == "left" else right)[0] = value
    with pytest.raises(ValueError, match="finite"):
        cosine_distance(left, right)


@pytest.mark.parametrize("scale", [1e308, 1e-308])
def test_cosine_preserves_geometry_at_extreme_finite_scales(scale: float) -> None:
    assert cosine_distance([scale, scale], [scale, 0]) == pytest.approx(1 - 2**-0.5)
    assert cosine_distance([scale, scale], [-scale, -scale]) == pytest.approx(2)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_dense_rejects_invalid_query_even_for_empty_corpus(bad: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        rank_dense([], "query", [bad], 1)


def test_dense_rejects_invalid_record_instead_of_ranking_it_first() -> None:
    records = [
        {"pathname": "good.mp4", "embedding": [1.0, 0.0]},
        {"pathname": "bad.mp4", "embedding": [float("nan"), 0.0]},
    ]
    with pytest.raises(ValueError, match=r"record 1.*finite"):
        rank_dense(records, "query", [1.0, 0.0], 2)
