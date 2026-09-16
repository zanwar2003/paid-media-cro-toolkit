"""
Paid Media Performance Analyzer
================================

Ingests a CSV of paid social campaign spend/results (the shape you'd export from
Meta Ads Manager, TikTok Ads Manager, or a blended reporting sheet) and computes the
core efficiency metrics media buyers actually make decisions on: CTR, CPC, CPA, and
ROAS, per campaign and per platform, then ranks campaigns from most to least efficient.

Usage:
    python ad_performance.py sample_data/campaigns.csv
    python ad_performance.py sample_data/campaigns.csv --sort-by roas --top 5
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CampaignResult:
    platform: str
    campaign: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    @property
    def ctr(self) -> float:
        """Click-through rate, as a percent of impressions."""
        return round((self.clicks / self.impressions) * 100, 2) if self.impressions else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return round(self.spend / self.clicks, 2) if self.clicks else 0.0

    @property
    def cpa(self) -> float:
        """Cost per acquisition (per conversion)."""
        return round(self.spend / self.conversions, 2) if self.conversions else 0.0

    @property
    def conversion_rate(self) -> float:
        """Conversions as a percent of clicks."""
        return round((self.conversions / self.clicks) * 100, 2) if self.clicks else 0.0

    @property
    def roas(self) -> float:
        """Return on ad spend: revenue generated per dollar spent."""
        return round(self.revenue / self.spend, 2) if self.spend else 0.0


def load_campaigns(path: str) -> list[CampaignResult]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            CampaignResult(
                platform=row["platform"],
                campaign=row["campaign"],
                spend=float(row["spend"]),
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                conversions=int(row["conversions"]),
                revenue=float(row["revenue"]),
            )
            for row in reader
        ]


def rank(campaigns: list[CampaignResult], sort_by: str, top: int | None) -> list[CampaignResult]:
    valid = {"roas", "cpa", "ctr", "cpc"}
    if sort_by not in valid:
        raise ValueError(f"--sort-by must be one of {sorted(valid)}")
    reverse = sort_by in {"roas", "ctr"}  # higher is better for these; lower is better for cpa/cpc
    ranked = sorted(campaigns, key=lambda c: getattr(c, sort_by), reverse=reverse)
    return ranked[:top] if top else ranked


def platform_rollup(campaigns: list[CampaignResult]) -> dict[str, dict[str, float]]:
    """Blended metrics per platform, computed from totals (not an average of averages)."""
    rollup: dict[str, dict[str, float]] = {}
    platforms = sorted({c.platform for c in campaigns})
    for platform in platforms:
        rows = [c for c in campaigns if c.platform == platform]
        spend = sum(c.spend for c in rows)
        clicks = sum(c.clicks for c in rows)
        impressions = sum(c.impressions for c in rows)
        conversions = sum(c.conversions for c in rows)
        revenue = sum(c.revenue for c in rows)
        rollup[platform] = {
            "spend": round(spend, 2),
            "ctr": round((clicks / impressions) * 100, 2) if impressions else 0.0,
            "cpc": round(spend / clicks, 2) if clicks else 0.0,
            "cpa": round(spend / conversions, 2) if conversions else 0.0,
            "roas": round(revenue / spend, 2) if spend else 0.0,
        }
    return rollup


def print_report(campaigns: list[CampaignResult], sort_by: str, top: int | None) -> None:
    print(f"Loaded {len(campaigns)} campaigns\n")

    print("Blended performance by platform:")
    for platform, m in platform_rollup(campaigns).items():
        print(
            f"  {platform:10s} spend=${m['spend']:>9,.2f}  CTR={m['ctr']:>5.2f}%  "
            f"CPC=${m['cpc']:>5.2f}  CPA=${m['cpa']:>6.2f}  ROAS={m['roas']:>4.2f}x"
        )

    print(f"\nTop campaigns by {sort_by}:")
    for c in rank(campaigns, sort_by, top):
        print(
            f"  [{c.platform:10s}] {c.campaign:28s} CTR={c.ctr:>5.2f}%  CPC=${c.cpc:>5.2f}  "
            f"CPA=${c.cpa:>6.2f}  ROAS={c.roas:>4.2f}x"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze paid social campaign performance.")
    parser.add_argument("campaigns_csv", help="Path to a campaign performance CSV")
    parser.add_argument(
        "--sort-by", default="roas", choices=["roas", "cpa", "ctr", "cpc"],
        help="Metric to rank campaigns by (default: roas)",
    )
    parser.add_argument("--top", type=int, default=None, help="Only show the top N campaigns")
    args = parser.parse_args(argv)

    campaigns = load_campaigns(args.campaigns_csv)
    print_report(campaigns, args.sort_by, args.top)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
