import pytest
from app.ranking.engine import calculate_jaccard_overlap

def test_jaccard_overlap():
    list_a = ["Running", "Photography", "Cooking"]
    list_b = ["trail running", "bouldering", "cooking"]
    
    score, shared = calculate_jaccard_overlap(list_a, list_b)
    assert score > 0.0
    assert "cooking" in shared or "Cooking" in [s.capitalize() for s in shared]
    assert any("running" in s for s in shared)

def test_jaccard_overlap_empty():
    score, shared = calculate_jaccard_overlap([], ["Music"])
    assert score == 0.0
    assert len(shared) == 0

def test_harmonic_mean_reciprocity():
    # Symmetric scores
    score_ab = 80.0
    score_ba = 80.0
    reciprocal = (2.0 * score_ab * score_ba) / (score_ab + score_ba)
    assert reciprocal == 80.0

    # Asymmetric scores: harmonic mean penalizes one-sided attraction
    score_ab = 90.0
    score_ba = 30.0
    reciprocal = (2.0 * score_ab * score_ba) / (score_ab + score_ba)
    assert reciprocal == 45.0
    # Arithmetic mean would be 60.0, harmonic mean correctly pulls it down to 45.0!
    assert reciprocal < ((score_ab + score_ba) / 2.0)
