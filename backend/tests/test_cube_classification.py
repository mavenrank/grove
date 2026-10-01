"""Source-observed cube/root arithmetic must not mix with painted cubes."""
import pytest

from ingestion.config import classify_title


@pytest.mark.parametrize("title", [
    "BSTS201P__17_10_22_CUBES_AND_CUBE_ROOTS",
    "Cubes & cube roots", "Cube-root shortcuts", "SQUARE_ROOTS", "Square roots and cubes",
])
def test_explicit_numeric_roots_are_arithmetic(title):
    assert classify_title(title) == ("quant.numbers.arithmetic", "active")


@pytest.mark.parametrize("title", ["030_CUBES_2023-08-02", "Painted cubes", "Dice", "Cubes and dice"])
def test_spatial_cubes_stay_reasoning(title):
    assert classify_title(title) == ("logic.pat.pattern_completion", "active")


def test_algorithm_scope_still_precedes_numeric_title_words():
    assert classify_title("Cube roots using binary search") == ("other.algorithms", "deferred")
