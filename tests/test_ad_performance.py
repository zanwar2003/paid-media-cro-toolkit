import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ad_performance import CampaignResult, platform_rollup, rank


def make(platform="Meta", campaign="Test", spend=100, impressions=10000, clicks=200, conversions=10, revenue=500):
    return CampaignResult(platform, campaign, spend, impressions, clicks, conversions, revenue)


def test_ctr_cpc_cpa_roas():
    c = make(spend=100, impressions=10000, clicks=200, conversions=10, revenue=500)
    assert c.ctr == 2.0
    assert c.cpc == 0.5
    assert c.cpa == 10.0
    assert c.roas == 5.0


def test_zero_impressions_does_not_divide_by_zero():
    c = make(impressions=0, clicks=0, conversions=0, revenue=0)
    assert c.ctr == 0.0
    assert c.cpc == 0.0
    assert c.cpa == 0.0
    assert c.roas == 0.0


def test_rank_sorts_roas_descending():
    low = make(campaign="Low", spend=100, revenue=100)   # roas 1.0
    high = make(campaign="High", spend=100, revenue=500)  # roas 5.0
    ranked = rank([low, high], sort_by="roas", top=None)
    assert [c.campaign for c in ranked] == ["High", "Low"]


def test_rank_sorts_cpa_ascending():
    cheap = make(campaign="Cheap", spend=100, conversions=50)   # cpa 2.0
    pricey = make(campaign="Pricey", spend=100, conversions=5)  # cpa 20.0
    ranked = rank([cheap, pricey], sort_by="cpa", top=None)
    assert [c.campaign for c in ranked] == ["Cheap", "Pricey"]


def test_platform_rollup_is_blended_not_averaged():
    a = make(platform="Meta", spend=100, clicks=100, conversions=10, revenue=500)
    b = make(platform="Meta", spend=300, clicks=300, conversions=10, revenue=300)
    rollup = platform_rollup([a, b])
    # blended CPA = total spend / total conversions = 400 / 20 = 20.0
    assert rollup["Meta"]["cpa"] == 20.0
