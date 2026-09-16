import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ab_test import Variant, two_proportion_z_test


def test_identical_rates_not_significant():
    control = Variant("Control", 5000, 500)
    variant = Variant("Variant", 5000, 500)
    result = two_proportion_z_test(control, variant)
    assert result.is_significant is False
    assert result.relative_lift_pct == 0.0


def test_large_clear_lift_is_significant():
    control = Variant("Control", 5000, 320)
    variant = Variant("Variant", 5100, 401)
    result = two_proportion_z_test(control, variant, confidence=0.95)
    assert result.is_significant is True
    assert result.relative_lift_pct > 0


def test_small_sample_lift_is_not_significant():
    control = Variant("Control", 60, 5)
    variant = Variant("Variant", 60, 8)
    result = two_proportion_z_test(control, variant, confidence=0.95)
    assert result.is_significant is False


def test_higher_confidence_is_harder_to_clear():
    control = Variant("Control", 5000, 320)
    variant = Variant("Variant", 5100, 370)
    at_90 = two_proportion_z_test(control, variant, confidence=0.90)
    at_99 = two_proportion_z_test(control, variant, confidence=0.99)
    # a result significant at 99% must also be significant at 90%, not necessarily the reverse
    if at_99.is_significant:
        assert at_90.is_significant
