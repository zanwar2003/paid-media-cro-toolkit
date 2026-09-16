# Paid Media & CRO Toolkit

A small, dependency-light toolkit for the two things a performance marketer actually needs to
answer day to day: *which campaigns are worth the spend*, and *did that landing-page change
actually move conversion rate, or is it noise*.

Three pieces:

- **`ad_performance.py`** — ingests a CSV export of paid social campaign results (the shape you'd
  get from Meta Ads Manager, TikTok Ads Manager, or a blended reporting sheet) and computes CTR,
  CPC, CPA, and ROAS per campaign and blended per platform, then ranks campaigns by whichever
  metric matters for the decision you're making.
- **`ab_test.py`** — a two-proportion z-test significance calculator for CRO experiments. Give it
  visitor/conversion counts for a control and a variant and it tells you whether a lift is real
  or within normal noise, at 90/95/99% confidence, without needing scipy.
- **`landing-page-demo/`** — a working, no-build-step example of the pattern in the browser: two
  landing-page variants, a visitor is assigned to one and stays there, clicks on the CTA are
  logged as conversions, and `results.html` runs the same statistics as `ab_test.py` (ported to
  JS) to call a winner once there's enough traffic.

## Why I built this

I wanted a from-scratch portfolio piece that shows the two halves of performance marketing I
find genuinely interesting: the media-buying side (which channel/creative is actually
efficient, not just which one has the most impressions) and the CRO side (is a landing-page
change a real improvement or a coin flip). This is original work built for this portfolio, not
production code from any employer.

## Usage

```bash
pip install -r requirements.txt

# Rank paid social campaigns by ROAS (or ctr / cpc / cpa)
python ad_performance.py sample_data/campaigns.csv --sort-by roas --top 5

# Check whether a CRO test result is statistically significant
python ab_test.py --control 5000 320 --variant 5100 401 --confidence 0.95
```

For the landing-page demo, open `landing-page-demo/index.html` directly in a browser (no server
needed — it's plain HTML/CSS/JS). Reload a few times in a private/incognito window to simulate
different visitors landing in each bucket, click the CTA on some of them, then open
`landing-page-demo/results.html` to see the live significance readout.

## Running the tests

```bash
pip install -r requirements.txt
pytest tests/
```

## Project structure

```
ad_performance.py              # CTR/CPC/CPA/ROAS calculator + campaign ranking + platform rollup
ab_test.py                     # two-proportion z-test significance calculator (CLI + importable)
sample_data/campaigns.csv      # synthetic 10-campaign dataset across Meta/Instagram/TikTok
tests/test_ad_performance.py   # unit tests for metric math, ranking, and platform rollups
tests/test_ab_test.py          # unit tests for the significance calculator
landing-page-demo/
  index.html                   # two-variant landing page with client-side bucket assignment
  results.html                 # live significance readout, pulling from the same experiment log
  experiment.js                # bucket assignment, event logging, and a JS port of the z-test
```

## Adapting this to a real pipeline

`load_campaigns()` reads CSV today; pointing it at the Meta/TikTok Marketing API or a warehouse
export is a matter of returning the same list of rows from a different loader. The landing-page
demo logs to `localStorage` for a zero-setup demo — swapping that for a real events table and an
API endpoint is the only change needed to run the same assignment/logging/analysis pattern
against live traffic.
