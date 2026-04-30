"""Gwet (2008) AC2 — paradox-robust inter-rater agreement.

Cohen's kappa exhibits the kappa paradox on skewed marginals : two raters
who agree 95% of the time can have kappa close to 0 if the prevalence is
skewed. Gwet's AC2 corrects this by recomputing chance agreement using
the marginal homogeneity assumption.

Use case in oracle harness :
- Per-scenario : n_votes=5 raters give binary verdict (pass/fail).
  Each scenario produces (n_pass, n_fail) with n_pass + n_fail = 5.
- Per-dim : aggregate across N scenarios for one dimension.
- Global  : aggregate across all dims.

Bootstrap 95% CI computed via percentile method (1000 resamples default).

Refs
----
- Gwet (2008) "Computing inter-rater reliability and its variance in the
  presence of high agreement", British Journal of Mathematical and
  Statistical Psychology 61, 29-48.
- Wongpakaran et al. (2013) "A comparison of Cohen's Kappa and Gwet's AC1
  when calculating inter-rater reliability coefficients : a study
  conducted with personality disorder samples", BMC Med Res Methodol.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class AC2Result:
    ac2: float
    ci_low: float
    ci_high: float
    n_items: int
    n_raters: int


def ac2_binary(items: list[tuple[int, int]]) -> float:
    """Compute Gwet's AC2 on binary multi-rater data.

    Parameters
    ----------
    items : list of (n_pass, n_fail) tuples
        Each tuple = vote counts for one item (scenario × dim).
        n_pass + n_fail must be constant across items (same n_raters).

    Returns
    -------
    float
        AC2 in [-1, 1]. 1.0 = perfect agreement, 0.0 = chance, < 0 = below chance.
    """
    N = len(items)
    if N == 0:
        return 0.0
    n_raters = items[0][0] + items[0][1]
    if n_raters < 2:
        return 0.0
    # Po — observed pairwise agreement
    po_num = sum(p * (p - 1) + f * (f - 1) for p, f in items)
    po_den = N * n_raters * (n_raters - 1)
    Po = po_num / po_den if po_den else 0.0
    # Pi — overall marginal probability (pass class)
    total_pass = sum(p for p, _ in items)
    pi_pass = total_pass / (N * n_raters)
    pi_fail = 1 - pi_pass
    # Pe Gwet (binary special case) — chance agreement under marginal homogeneity
    Pe = 2 * pi_pass * pi_fail
    if Pe >= 1.0:
        return 1.0
    return (Po - Pe) / (1 - Pe)


def ac2_with_ci(
    items: list[tuple[int, int]],
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int | None = None,
) -> AC2Result:
    """Compute AC2 with bootstrap percentile CI.

    Parameters
    ----------
    items : list of (n_pass, n_fail)
    n_boot : number of bootstrap resamples
    ci : confidence level in (0, 1)
    seed : reproducibility seed for bootstrap

    Returns
    -------
    AC2Result
    """
    point = ac2_binary(items)
    if not items:
        return AC2Result(ac2=0.0, ci_low=0.0, ci_high=0.0, n_items=0, n_raters=0)
    rng = random.Random(seed)
    N = len(items)
    n_raters = items[0][0] + items[0][1]
    boots: list[float] = []
    for _ in range(n_boot):
        sample = [items[rng.randrange(N)] for _ in range(N)]
        boots.append(ac2_binary(sample))
    boots.sort()
    alpha = (1 - ci) / 2
    low_idx = int(alpha * n_boot)
    high_idx = int((1 - alpha) * n_boot) - 1
    high_idx = max(high_idx, low_idx)
    low = boots[low_idx]
    high = boots[high_idx]
    return AC2Result(
        ac2=point,
        ci_low=low,
        ci_high=high,
        n_items=N,
        n_raters=n_raters,
    )


def aggregate_per_dim(
    verdicts_by_dim: dict[str, list[tuple[int, int]]],
    n_boot: int = 1000,
    seed: int | None = None,
) -> dict[str, AC2Result]:
    """Compute AC2 per dimension. Convenience wrapper for harness output."""
    return {
        dim: ac2_with_ci(items, n_boot=n_boot, seed=seed)
        for dim, items in verdicts_by_dim.items()
    }


def aggregate_global(
    verdicts_by_dim: dict[str, list[tuple[int, int]]],
    n_boot: int = 1000,
    seed: int | None = None,
) -> AC2Result:
    """Compute AC2 across all dims (flat concat)."""
    flat: list[tuple[int, int]] = []
    for items in verdicts_by_dim.values():
        flat.extend(items)
    return ac2_with_ci(flat, n_boot=n_boot, seed=seed)
