"""
CRO A/B Test Significance Calculator
=====================================

Takes visitor/conversion counts for a control landing page and one or more test
variants and runs a two-proportion z-test to say whether a lift is statistically
significant, or just noise, before you ship a landing-page change.

Usage:
    python ab_test.py --control 5000 320 --variant 5100 401
    python ab_test.py --control 5000 320 --variant 5100 401 --confidence 0.99
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass
class Variant:
    name: str
    visitors: int
    conversions: int

    @property
    def rate(self) -> float:
        return self.conversions / self.visitors if self.visitors else 0.0


@dataclass
class SignificanceResult:
    control: Variant
    variant: Variant
    z_score: float
    p_value: float
    confidence: float
    is_significant: bool
    relative_lift_pct: float

    def summary(self) -> str:
        winner = self.variant.name if self.relative_lift_pct > 0 else self.control.name
        verdict = (
            f"significant at {self.confidence * 100:.0f}% confidence — ship {winner}"
            if self.is_significant
            else "not statistically significant — keep collecting data before deciding"
        )
        return (
            f"{self.control.name}: {self.control.conversions}/{self.control.visitors} "
            f"({self.control.rate:.2%})\n"
            f"{self.variant.name}: {self.variant.conversions}/{self.variant.visitors} "
            f"({self.variant.rate:.2%})\n"
            f"Relative lift: {self.relative_lift_pct:+.1f}%  |  z={self.z_score:.2f}  "
            f"p={self.p_value:.4f}\n"
            f"Result: {verdict}"
        )


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via the complementary error function (no scipy dependency)."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _z_critical(confidence: float) -> float:
    """Two-tailed z critical value for a small, fixed set of common confidence levels."""
    table = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    closest = min(table, key=lambda k: abs(k - confidence))
    return table[closest]


def two_proportion_z_test(control: Variant, variant: Variant, confidence: float = 0.95) -> SignificanceResult:
    p1, n1 = control.rate, control.visitors
    p2, n2 = variant.rate, variant.visitors

    pooled_p = (control.conversions + variant.conversions) / (n1 + n2)
    se = math.sqrt(pooled_p * (1 - pooled_p) * (1 / n1 + 1 / n2))

    z = 0.0 if se == 0 else (p2 - p1) / se
    p_value = 2 * (1 - _norm_cdf(abs(z)))
    is_significant = abs(z) >= _z_critical(confidence)
    relative_lift_pct = ((p2 - p1) / p1) * 100 if p1 else 0.0

    return SignificanceResult(
        control=control,
        variant=variant,
        z_score=round(z, 4),
        p_value=round(p_value, 4),
        confidence=confidence,
        is_significant=is_significant,
        relative_lift_pct=round(relative_lift_pct, 2),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Two-proportion z-test for a CRO A/B test.")
    parser.add_argument("--control", nargs=2, type=int, metavar=("VISITORS", "CONVERSIONS"), required=True)
    parser.add_argument("--variant", nargs=2, type=int, metavar=("VISITORS", "CONVERSIONS"), required=True)
    parser.add_argument("--confidence", type=float, default=0.95, choices=[0.90, 0.95, 0.99])
    args = parser.parse_args(argv)

    control = Variant("Control", *args.control)
    variant = Variant("Variant", *args.variant)
    result = two_proportion_z_test(control, variant, confidence=args.confidence)
    print(result.summary())
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
