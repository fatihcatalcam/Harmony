import pytest

from types import SimpleNamespace

from harmony.routes.main import calculate_blend_score


def make_user(artists=None, tracks=None, genres=None):
    return SimpleNamespace(top_artists=artists, top_tracks=tracks, genres=genres)


def test_calculate_blend_score_identical_preferences():
    artists = [
        {"name": "Artist One"},
        {"name": "Artist Two"},
    ]
    tracks = [
        {"name": "Track A"},
        {"name": "Track B"},
    ]
    genres = ["Pop", "Indie"]

    user = make_user(artists=artists, tracks=tracks, genres=genres)
    candidate = make_user(artists=artists, tracks=tracks, genres=genres)

    score = calculate_blend_score(user, candidate)
    assert score == pytest.approx(1.0)


def test_calculate_blend_score_partial_overlap():
    current_user = make_user(
        artists=[
            {"name": "Artist One"},
            {"name": "Artist Two"},
            {"name": "Artist Three"},
        ],
        tracks=[
            {"name": "Track A"},
            {"name": "Track B"},
            {"name": "Track C"},
        ],
        genres=[["Pop", "Rock"]],
    )

    candidate = make_user(
        artists=[
            {"name": "Artist One"},
            {"name": "Artist Four"},
            {"name": "Artist Five"},
        ],
        tracks=[
            {"name": "Track A"},
            {"name": "Track D"},
            {"name": "Track E"},
        ],
        genres=[["Rock", "Jazz"]],
    )

    score = calculate_blend_score(current_user, candidate)

    expected = 0.4 * (1 / 5) + 0.4 * (1 / 5) + 0.2 * (1 / 3)
    assert score == pytest.approx(expected)


def test_calculate_blend_score_no_data_returns_zero():
    user = make_user()
    candidate = make_user()

    assert calculate_blend_score(user, candidate) == 0.0
