/**
 * Minimal client-side A/B test harness for a landing page CRO experiment.
 *
 * - Assigns each new visitor to "control" or "variant" (persisted in localStorage so a
 *   repeat visitor always sees the same version — no flip-flopping mid-experiment).
 * - Logs an impression on load and a conversion whenever the primary CTA is clicked.
 * - Ships the same two-proportion z-test math as ab_test.py so results.html can call out
 *   a winner once there's enough traffic, instead of eyeballing raw percentages.
 *
 * No backend required: everything lives in localStorage, which is enough for demoing the
 * pattern. Swapping localStorage for a real events table/API is the only change needed to
 * run this against live traffic.
 */

const STORAGE_KEY = "cro_demo_log";

function getLog() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || { control: { impressions: 0, conversions: 0 }, variant: { impressions: 0, conversions: 0 } };
  } catch {
    return { control: { impressions: 0, conversions: 0 }, variant: { impressions: 0, conversions: 0 } };
  }
}

function saveLog(log) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(log));
}

function assignBucket() {
  let bucket = localStorage.getItem("cro_demo_bucket");
  if (!bucket) {
    bucket = Math.random() < 0.5 ? "control" : "variant";
    localStorage.setItem("cro_demo_bucket", bucket);
  }
  return bucket;
}

function recordImpression(bucket) {
  const log = getLog();
  log[bucket].impressions += 1;
  saveLog(log);
}

function recordConversion(bucket) {
  const log = getLog();
  log[bucket].conversions += 1;
  saveLog(log);
}

function initExperiment(onAssigned) {
  const bucket = assignBucket();
  recordImpression(bucket);
  document.body.dataset.variant = bucket;
  if (typeof onAssigned === "function") onAssigned(bucket);

  document.querySelectorAll("[data-cro-cta]").forEach((el) => {
    el.addEventListener("click", () => {
      recordConversion(bucket);
      el.textContent = "Thanks — you're on the list!";
      el.disabled = true;
    });
  });
}

// --- same statistics as ab_test.py, ported to JS so results.html needs no build step ---

function normCdf(x) {
  return 0.5 * (1 + erf(x / Math.sqrt(2)));
}

function erf(x) {
  // Abramowitz-Stegun approximation, accurate to ~1e-7 — plenty for a demo significance check.
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const t = 1 / (1 + p * x);
  const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y;
}

function zCritical(confidence) {
  const table = { 0.9: 1.645, 0.95: 1.96, 0.99: 2.576 };
  return table[confidence] ?? 1.96;
}

function twoProportionZTest(control, variant, confidence = 0.95) {
  const p1 = control.impressions ? control.conversions / control.impressions : 0;
  const p2 = variant.impressions ? variant.conversions / variant.impressions : 0;
  const n1 = control.impressions, n2 = variant.impressions;
  const pooled = (control.conversions + variant.conversions) / (n1 + n2 || 1);
  const se = Math.sqrt(pooled * (1 - pooled) * (1 / (n1 || 1) + 1 / (n2 || 1)));
  const z = se === 0 ? 0 : (p2 - p1) / se;
  const pValue = 2 * (1 - normCdf(Math.abs(z)));
  const isSignificant = Math.abs(z) >= zCritical(confidence);
  const relativeLiftPct = p1 ? ((p2 - p1) / p1) * 100 : 0;
  return { p1, p2, z, pValue, isSignificant, relativeLiftPct, confidence };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { getLog, saveLog, assignBucket, recordImpression, recordConversion, twoProportionZTest };
}
