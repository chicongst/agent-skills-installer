---
name: algorithm-review
description: Use when reviewing code for algorithmic complexity — nested loops, repeated scans, wrong data structure, brute force where a known algorithm (hashing, sorting, binary search, prefix sums, heaps, graph traversal) would change the Big-O. Proposes behavior-preserving rewrites verified against the original. Not for profiling a running system or diagnosing slow queries and N+1 (use `performance-review`), schema or index design (use `db-design`), general bug review (use `code-review`), or applying the change (hand the verified rewrite to `refactor`).
---

# Algorithm Review

Review code for places where a better algorithm or data structure changes the complexity at the scale the code actually runs at. This is a review skill: propose rewrites in the report; do not edit the user's files.

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors the Output Format below.

## Core Rules

1. **Scale first.** Before judging, establish n (and m, k…), call frequency, and whether the path is hot. Take them from the input or code; if unknown, ask the user (use AskUserQuestion if available, otherwise ask in plain text) or state an explicit assumption in the report. Without scale, a finding is at most 🟡 MINOR, unless untrusted input controls n (see BLOCKER).
2. **Complexity claims must be exact.** Count every term, including hidden costs (see table below) and output size. If the output itself can be O(n²), no behavior-preserving rewrite beats O(n²) — say "O(n + D) where D = output size", not "O(n)". Say amortized/expected where it applies (hash maps, union-find).
3. **Every rewrite must preserve behavior.** The optimized code must return the same result (same values, same order, same multiplicity, same exceptions) as the original for every input the original accepts — work through the edge-case checklist below.
4. **Verify by running old vs new.** When you can execute code, write a throwaway harness outside the repo (a temp dir) that runs the original and the rewrite on the same inputs — hand-picked edge cases plus randomized inputs — and asserts equal output. Report what was run. If you cannot execute, mark the finding `Equivalence: NOT verified` and include the harness for the user to run.
5. **Behavior changes are separate.** If the original looks buggy (e.g. emits a duplicate twice) or preservation is impossible, do not fold a "fix" into the optimization. List it under **Behavior changes / questions** and let the user decide. An optimization that silently changes output is a defect, not a finding.
6. **No invented measurements.** Big-O and operation counts derived from stated sizes are fine. Wall-clock numbers only if the input provides them; otherwise label them "estimate". For profiling, route to `performance-review`.
7. **Say when it's fine.** Small bounded n, cold paths, or a rewrite that costs more readability than it saves: list under **Fine as-is** with the reason.

## Edge-Case Checklist (for every rewrite)

| Case | What typically breaks |
|------|-----------------------|
| Duplicates / multiplicity | Set-based dedup emits each item once where the original emitted per pair; counts collapse |
| Missing keys / `None` / unknown references | Original skipped or never touched a field (short-circuit, empty loop); rewrite indexes it eagerly → `KeyError`/NPE, or silently drops rows the original kept |
| Empty input, single element | Rewrite touches data the original never read; `max()` of empty; off-by-one in index arrays |
| Ordering and ties | Set/hash iteration order differs; unstable sort; heap tie-breaking differs from stable sort; top-k with equal counts |
| Absent groups | Original emitted zero-count entries; `Counter`/`groupBy` only has keys that occurred |
| Inverted or out-of-range bounds | `start > end`, bounds outside the data; prefix-sum difference goes negative |
| Equality semantics | Hashing vs `==` (NaN, `1 == 1.0 == True`, case, custom `__eq__`), unhashable keys |
| Floating point | Reordered additions (prefix sums, parallel reduce) are not bit-identical |
| Identity and mutation | Original returned the same objects vs copies; rewrite mutates input or shares state |
| Iterators / side effects | Rewrite iterates a one-shot iterator twice; early exit skips side effects the original ran |
| Staleness | Precomputed index/cache not invalidated when the source data changes |

If the rewrite relies on an assumption (e.g. "ids are ints and always present"), state it in the finding.

## Workflow

1. **Scope** — list the functions in scope, the scale for each, and which run hot (loops, per-request, per-row).
2. **Spot signals** — nested loops over the same or related collections, lookups inside loops, repeated recomputation, sorting inside a loop, brute-force enumeration, recursion with overlapping subproblems.
3. **Derive current complexity** — including hidden costs.
4. **Pick the smallest rewrite** that removes the dominant term. Prefer the language's standard library over hand-rolled structures.
5. **Audit edge cases, then run the equivalence harness** (Rules 3–4).
6. **Rank** by impact at stated scale and assign severity.

## Hidden Costs to Count

| Construct | Cost |
|-----------|------|
| Python `x in list`, `list.index`, `list.remove`, `list.pop(0)`, `list.insert(0, x)` | O(n) — use `set`/`dict`, `collections.deque` |
| JS `arr.includes/indexOf/find` in a loop; `arr.shift()`; `[...acc, x]` or `{...acc}` in `reduce` | O(n) each → O(n²) overall |
| Java `List.contains`, `ArrayList.remove(0)`; C# `List.Contains`, `RemoveAt(0)`; C# re-enumerating an `IEnumerable` (`.Count()`, `.ElementAt(i)`) inside a loop | O(n) each |
| String concatenation in a loop (most languages) | O(n²) worst case — use a builder / `join` |
| Slicing / copying inside a loop | O(k) per iteration |
| Sorting inside a loop | O(n log n) per iteration — sort once outside |
| DB/HTTP call inside a loop | Not an algorithm issue — route to `performance-review` (N+1, slow queries) or `db-design` (missing indexes) |

## Technique Reference

Complexities are for the operation named; include build cost when a structure is built for a single use.

- **Hash map / set** — expected O(1) lookup instead of O(n) scan. Signals: lookup or `contains` inside a loop, pairwise comparison to find matches, manual grouping. Needs hashable keys with consistent equality.
- **Frequency map / group-by** — one O(n) pass instead of one scan per group. Remember groups with zero occurrences.
- **Sort + scan / two pointers** — O(n log n) once, then linear passes: pairs in sorted data, merging, nearest value, interval overlap.
- **Binary search** — O(log n) per query on sorted data. Only a win if the data is already sorted or queried many times; sorting for one lookup is worse than a scan.
- **Heap / priority queue** — top-k in O(n log k); repeated min/max with inserts in O(log n) each instead of re-sorting.
- **Prefix sums** — O(n) build; range sum is O(1) on a dense index (array indexed by position/day), O(log d) with binary search over sparse sorted keys. Integer/exact types only if results must be identical.
- **Sliding window** — O(n) for moving sums/counts; monotonic deque for window max/min.
- **Counting / bucket sort** — O(n + k) when values fall in a small known range k.
- **Topological sort (Kahn's)** — O(V + E) dependency ordering; reports cycles instead of looping until "everything resolves".
- **BFS / DFS** — O(V + E); BFS for unweighted shortest paths.
- **Dijkstra** — O((V + E) log V) with a binary heap; non-negative weights only (negative weights → Bellman-Ford).
- **Union-find** — near-constant amortized per op (with path compression + union by rank) for dynamic connectivity instead of repeated BFS.
- **Trie** — prefix lookup without scanning every string.
- **Memoization / DP** — overlapping subproblems in pure functions; bound the cache.
- **Greedy** — only when an exchange argument proves it optimal (interval scheduling, Huffman). Coin change is greedy-optimal only for canonical coin systems; otherwise DP.
- **String search** — standard library `find`/`indexOf` is already efficient for typical inputs; hand-written KMP/Rabin-Karp only for measured bottlenecks or multi-pattern search (Aho-Corasick).

## Severity

Same four levels as `code-audit`, applied to complexity:

- **🔴 BLOCKER** — at stated scale the path exceeds a stated time/memory limit, or untrusted input can trigger super-linear work (algorithmic DoS: O(n²) on request payloads, catastrophic regex backtracking).
- **🟠 MAJOR** — hot path at stated scale where a standard technique removes a factor of n (or more).
- **🟡 MINOR** — real improvement but small at current scale, or matters only if scale grows or call frequency rises.
- **💭 NIT** — data-structure choice that improves readability with no meaningful cost difference.

## Output Format

```markdown
# Algorithm Review: [scope]

**Scale**: [n, m, call frequency per function — "from input" or "assumed: …"]
**Verdict**: [Optimize now / Optimize if scale grows / Fine as-is] — [one sentence]

## Findings

### [🔴/🟠/🟡/💭] [Short title]
**Location**: [file:line–line or function name]
**Signal**: [the pattern that triggered this finding]
**Current**: [O(...) — which term dominates, with operation count at stated scale]
**Proposed**: [O(...) — technique name]

Before:
[original code, or the relevant lines]

After:
[rewrite]

**Edge cases checked**: [duplicates, missing keys, empty input, ordering/ties, … — and how each is preserved; assumptions stated]
**Equivalence**: [what was run — edge cases + N randomized inputs, old vs new, all equal] or [NOT verified — harness below]
**Behavior changes / questions**: [None, or what the user must decide]

## Fine As-Is
- [function/location] — [why no change is needed]

## Top Priorities
1. [Most impactful change]
2. [...]
```

Order findings by severity, then by impact. Omit **Fine As-Is** if empty. Keep **Top Priorities** to 1–5 items.
