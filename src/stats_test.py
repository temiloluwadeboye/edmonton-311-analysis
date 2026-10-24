"""Statistical test: are pothole response times really different between wards?

Run from the project root:
    python -m src.stats_test

Output: printed results + results/stats_test.json

Why these tests
---------------
Response times are heavily SKEWED: most pothole tickets close in a few days, but a few
take months or years (the 90th percentile is 35-77 days depending on the ward). The common
tests, the t-test and ANOVA, compare AVERAGES and assume the data roughly follows a bell
curve. Neither holds here: the averages are pulled up by a few extreme tickets.

So both tests below are RANK-BASED ("non-parametric"): they line up every ticket from
fastest to slowest and compare the groups' POSITIONS in that line, not the raw days.
A single 4,000-day ticket counts as "the slowest", not as 4,000, so it can't distort the result.

* Kruskal-Wallis: the rank-based alternative to one-way ANOVA. It compares MORE THAN TWO
  groups at once (our 12 wards) and asks: "is there a difference anywhere among them?"
  Running 66 separate two-ward tests instead would inflate the chance of a false alarm.

* Mann-Whitney U: the rank-based alternative to the two-sample t-test. It compares exactly
  TWO groups. We use it after Kruskal-Wallis for the fastest vs the slowest ward, because
  its statistic converts directly into an easy-to-explain effect size: the probability that
  a random ticket from one ward is closed before a random ticket from the other.

With 33,000+ tickets almost any difference is "statistically significant", so the
effect sizes (epsilon squared and that probability) matter more than the p-values.
"""

import json
import statistics
from pathlib import Path

import duckdb
import numpy as np
from scipy import stats

from src.load import DB_PATH

RESULTS_PATH = Path("results/stats_test.json")
ALPHA = 0.05   # significance cut-off, chosen BEFORE looking at the results

# Same rows as step 1 of sql/04_ward_response_times.sql
POTHOLE_QUERY = """
    SELECT ward, days_to_close
    FROM requests
    WHERE year >= 2022
      AND status = 'Closed'
      AND NOT closed_without_date
      AND (status_detail IS NULL OR status_detail NOT LIKE 'Duplicate%')
      AND ward_system = 'new'
      AND category = 'Potholes'
"""


def load_ward_times():
    """Run POTHOLE_QUERY and return a dict: {ward name: list of days_to_close}.

    Hint: con.execute(POTHOLE_QUERY).df() gives a DataFrame; then
    df.groupby("ward")["days_to_close"] lets you build the dict,
    e.g. {ward: group.tolist() for ward, group in df.groupby("ward")["days_to_close"]}
    Open the database with read_only=True (we're only reading).
    """
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        data = con.execute(POTHOLE_QUERY).df() 
    ward_days = data.groupby("ward")["days_to_close"]
    return {ward: group.tolist() for ward, group in ward_days}


def kruskal_wallis(ward_times):
    """Kruskal-Wallis test across ALL wards. Return (H statistic, p-value).

    Hint: stats.kruskal(*ward_times.values())
    The * unpacks the dict's lists into separate arguments: kruskal(list1, list2, ...).
    """
    return stats.kruskal(*ward_times.values())


def epsilon_squared(h, n):
    """Effect size for Kruskal-Wallis: roughly the share of the variation in response
    times that is explained by ward (0 = none, 1 = all).

    Formula: epsilon² = H / (n - 1), where n is the total number of tickets.
    Rough guide: < 0.01 negligible, 0.01-0.08 small, 0.08-0.26 medium, > 0.26 large.
    """
    return h / (n - 1)


def chance_faster(times_a, times_b):
    """Mann-Whitney U test between two wards. Return (p-value, probability that a
    random ticket from A is closed sooner than a random ticket from B).

    Hint: result = stats.mannwhitneyu(times_b, times_a)
    Putting B first makes result.statistic count the pairs where A is faster (B's time
    is larger). Divide by len(times_a) * len(times_b) to turn the count into a probability.
    Ties (same day) count as half, which mannwhitneyu already handles.
    """
    # B first: the statistic counts pairs where B's ticket took longer, i.e. A was faster
    result = stats.mannwhitneyu(times_b, times_a)
    probability = result.statistic / (len(times_a) * len(times_b))
    return result.pvalue, probability


def effect_size_label(eps2):
    """Turn epsilon squared into a word, using the rough guide in epsilon_squared()."""
    if eps2 < 0.01:
        return "negligible"
    if eps2 < 0.08:
        return "small"
    if eps2 < 0.26:
        return "medium"
    return "large"


def main():
    # Step 1: load the ward times
    ward_times = load_ward_times()
    n = sum(len(times) for times in ward_times.values())
    print(f"Pothole tickets: {n:,} across {len(ward_times)} wards\n")

    # Step 2: Kruskal-Wallis across all wards
    h, p_all = kruskal_wallis(ward_times)
    significant = p_all < ALPHA
    print("Kruskal-Wallis (are there differences anywhere among the wards?)")
    print(f"  H = {h:,.1f}, p = {p_all:.2e} -> {'significant' if significant else 'not significant'} at alpha = {ALPHA}")

    # Step 3: effect size for the overall test
    eps2 = epsilon_squared(h, n)
    print(f"  Effect size: epsilon squared = {eps2:.3f} ({effect_size_label(eps2)}): "
          f"ward explains about {eps2:.0%} of the variation in response times\n")

    # Step 4: fastest vs slowest ward. Rank by median, then by 90th percentile to break
    # ties, the same way as sql/04_ward_response_times.sql
    summary = {
        ward: (statistics.median(times), np.percentile(times, 90))
        for ward, times in ward_times.items()
    }
    ranked = sorted(summary, key=summary.get)
    fastest, slowest = ranked[0], ranked[-1]
    p_pair, prob = chance_faster(ward_times[fastest], ward_times[slowest])
    print(f"Mann-Whitney U: fastest ward ({fastest}, median {summary[fastest][0]:.0f} days) "
          f"vs slowest ward ({slowest}, median {summary[slowest][0]:.0f} days)")
    print(f"  p = {p_pair:.2e}")
    print(f"  A random pothole ticket in {fastest} is closed before one in {slowest} "
          f"{prob:.0%} of the time (50% would mean no difference).")

    # Step 5: save the numbers for the README and dashboard
    results = {
        "tickets": n,
        "wards": len(ward_times),
        "alpha": ALPHA,
        "kruskal_wallis": {"H": round(h, 2), "p_value": p_all, "significant": bool(significant)},
        "epsilon_squared": round(eps2, 4),
        "effect_size": effect_size_label(eps2),
        "fastest_ward": {"ward": fastest, "median_days": summary[fastest][0]},
        "slowest_ward": {"ward": slowest, "median_days": summary[slowest][0]},
        "mann_whitney": {"p_value": p_pair, "prob_fastest_closes_first": round(prob, 3)},
    }
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {RESULTS_PATH}")


if __name__ == "__main__":
    main()
