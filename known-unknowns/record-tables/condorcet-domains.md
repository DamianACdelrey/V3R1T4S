# Condorcet domains: a larger domain than the best published one for some n in 9..25

📊 **Record tables** · harvest (many cells or partial wins within reach) · tractability ★★★☆☆ · compute: laptop-hours · open as of 2026-10-24

## The problem

A Condorcet domain on n alternatives is a set of linear orders such that the pairwise majority relation of every profile with an odd number of voters drawn from the set is transitive. Equivalently (Sen 1966), the restriction to every triple of alternatives satisfies a never condition: some alternative of the triple is never first, never middle or never last within that triple. The maximum size is known exactly only for n <= 8 (1, 2, 4, 9, 20, 45, 100, 224; n = 8 by Leedham-Green, Markstrom and Riis, arXiv:2303.15002; all maximal domains for n <= 7 by Akello-Egwel, Leedham-Green, Litterick, Markstrom and Riis, Math. Soc. Sci. 2024). Fishburn's alternating scheme (Social Choice and Welfare 14 (1996) 113-124) gave the long-standing values (488 for n = 9, 1069 for n = 10, 2324 for n = 11); Zhou and Riis (arXiv:2303.06524) raised n = 10 to 1082 and n = 11 to 2349; Karpov and Slinko (Theory and Decision 2023) gave a product construction and the asymptotic bound 2.1890^n; Karpov, Markstrom, Riis and Zhou (arXiv:2308.02817, Discrete Applied Mathematics 370 (2025) 57-70) introduced set-alternating schemes and coherent domains of size above 2.1973^n. The current table is Table 4 of Karpov, Markstrom, Riis and Zhou, 'Improved lower bounds for the maximum size of Condorcet domains', arXiv:2601.07336v1 (12 Jan 2026): for n = 9..20 an inductive search on a supercomputer (stopped at n = 20) gave 492, 1104, 2452, 5520, 12182, 27026, 59430, 131536, 292015, 649079, 1432836, 3155366; for n = 21..25 the Karpov-Slinko construction applied to those domains gave 6674931, 15037178, 33162136, 73279872, 160316046 (marked ks); the asymptotic bound is now Omega(2.198139^n). As of 2026-10-24 the abstract page lists v1 only. Find a larger domain for some n in 9..25.

## What counts as a win

(1) The object is a never-condition assignment A: exactly one line 'a b c iNj' for each of the C(n,3) triples a < b < c of 1..n, meaning the i-th smallest of {a,b,c} is never in position j (1 = top, 3 = bottom) within the triple. The claimed domain is D(A), the set of ALL linear orders of 1..n obeying every line; it is a Condorcet domain by Sen's theorem, so no separate acyclicity check is needed. This loses no generality: every Condorcet domain lies inside D(A) for an assignment A it satisfies. (2) |D(A)| is counted exactly (not sampled, not estimated) by two independent implementations, for example a forward DP over prefix sets, and both agree with the claimed value. (3) n is in 9..25 and |D(A)| is STRICTLY GREATER (direction: max) than every one of the following, each re-checked at verification time: the n entry of Table 4 of the latest version of arXiv:2601.07336 (status_source; v1 values: n=9 492, 10 1104, 11 2452, 12 5520, 13 12182, 14 27026, 15 59430, 16 131536, 17 292015, 18 649079, 19 1432836, 20 3155366, 21 6674931, 22 15037178, 23 33162136, 24 73279872, 25 160316046), any larger value found by a fresh search of arXiv and the 2025-2026 literature, and any value for the same n already in TROPHY_CASE.md or known-knowns/condorcet-domains/. If the status source cannot be read honestly, the claim is 'PENDING TABLE CHECK', not a record. (4) An explicit list of orders is optional; if shipped it must obey kit/SUBMIT.md (files at most 1 MB, packages at most 50 MB, larger files outside git), and the assignment remains the object that is judged.

## Partial wins

- **p1:** Problem 2 of arXiv:2601.07336: determine h(9), the maximum size of a peak-pit Condorcet domain on 9 alternatives, or g_w(9), the maximum size of a Condorcet domain of maximum width (one containing an order and its reverse) on 9 alternatives, by a re-checkable certificate (an exhaustive search with its full log and an independent re-run, or a DRAT/LRAT proof checked with an independent checker); or prove an upper bound on h(9) or g_w(9) smaller than every upper bound published for it at verification time.

## How a win is checked

The verifier writes an independent standard-library checker and does not run the claimant's code: parse the assignment, require exactly one well-formed line per triple (no missing, duplicate or out-of-range triples), then count D(A) by a forward DP over prefix sets: from a placed set S, alternative v may come next unless some line on a triple {v,x,y} forbids v at position 1 + |{x,y} intersect S|; sum counts into S | {v}; |D(A)| is the count at the full set. Only reachable prefix sets need storing (a few thousand for n <= 25), so this runs in seconds in Python. Cross-check the DP with a second method: brute-force enumeration of the restriction of A to the first 9 alternatives must equal the DP count of that restriction, and the DP on Fishburn's alternating scheme (middle element of {a,b,c} never first if b is even, never last if b is odd) must give 488 for n = 9 and 2115186 for n = 20 (Table 4's Fishburn column). Then re-fetch the status source and the trophy case, and claim only if |D(A)| is strictly larger than all of them and equals the claimed value.

## Is it still open?

Check the status page before you start and again before you claim anything; tables move fast.

- <https://arxiv.org/abs/2601.07336>

## Sources

- <https://arxiv.org/abs/2601.07336>
- <https://arxiv.org/abs/2308.02817>
- <https://doi.org/10.1016/j.dam.2025.03.007>
- <https://arxiv.org/abs/2303.06524>
- <https://arxiv.org/abs/2303.15002>
- <https://doi.org/10.1007/s11238-022-09878-9>
- <https://doi.org/10.1007/s003550050055>

## Ideas to start from

Starting points, not instructions. The best wins came from angles nobody listed.

- Search over assignments, not over lists of orders: D(A) is determined by one never condition per triple and can be counted exactly in milliseconds, so the objective is cheap and exact inside any local search.
- Large-neighbourhood search: re-optimise every triple through one or two chosen alternatives at once, exactly (branch and bound or ILP), instead of single-triple moves.
- Restrict and extend: delete one alternative from a strong domain on n+1 alternatives, or apply the paper's one-alternative extension step to a strong domain on n-1, then polish.
- Rows n = 21..25 of the paper's table come from a product construction rather than search, so they are softer than the n <= 20 rows.
- Use the structure of the known maxima (peak-pit conditions 1N3 and 3N1, with some 2N1 and 2N3) as a prior rather than a constraint.

## Traps

False wins others have fallen for. A claim that walks into one of these will not survive the skeptics.

- Counting the orders of an assignment with a missing or duplicated triple gives a set that need not be a Condorcet domain; require exactly C(n,3) distinct triples.
- Position conventions: whether 1 means top or bottom does not change |D(A)| (reversal is a bijection), but the checker and the claim must use one convention consistently.
- Table 4 has other columns (Fishburn's scheme, a formula column ceil((4/5^1.5) * sqrt(5)^n), g(n) for peak-pit domains of maximal width); the record is the f(n) & h(n) column only.
- Matching a table value is not a record; neither is a value for n >= 26, where the table has no cell.
- Estimating |D(A)| by sampling or by enumerating with a time limit is not an exact count.
- The paper's search rows may be superseded by a v2 or a follow-up; always re-read the abstract page's submission history before claiming.

## Point your agent at it

```
set up V3R1T4S: https://github.com/elder-plinius/V3R1T4S and hunt known-unknowns/record-tables/condorcet-domains.md
```

Already set up? Say `run V3R1T4S on condorcet-domains`. Your agent follows [AGENTS.md](../../AGENTS.md): it re-checks the status, freezes its success rule, attacks, and only a three-skeptic panel can confirm a win.

---

_Generated from [`bank/targets.json`](../../bank/targets.json) (id `condorcet-domains`). Found it solved, stale or wrong? Open an issue or a pull request against that file._
