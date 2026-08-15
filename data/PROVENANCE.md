# Data Provenance

This file records the canonical SHA-256 hashes and provenance notes for every
data file the ScriptureVec Justice paper depends on. Every paper-facing
number was produced from the files at the hashes listed below.

## Bundled Files

| File | Bytes (approx) | SHA-256 | Role |
| --- | --- | --- | --- |
| `bible_kjv.json` | ~5.7 MB | `e7c9adaa37ac0cce353d7c1cb78d001e02df672ce64c027897f602afa97c40e1` | Bundled King James Version. Source corpus for every book and chapter target. |
| `justice/scenarios.csv` | ~0.4 MB | `cfc7550bf47fa9a8b60882a7872e729441cd9d90ba5f4efe3f62cdac2faf9504` | VirtueBench V2 Justice scenarios. 150 base scenarios × 5 variants (ratio, caro, mundus, diabolus, ignatian) = 750 rows + header. The paper uses the *ratio* variant only (150 items). Limit-10 screens use items 0–9; limit-40 confirmation uses items 0–39 under `seed=42` (paper §3.5). |
| `courage/scenarios.csv` | ~0.4 MB | `1a5c44819c02a1e03d087e1e6715dfd2b5a657f7013c5cbdc635198f189468ff` | VirtueBench V2 Courage scenarios. Same 150 × 5 structure. Not used in the paper headline; bundled because the codebase is shared with the broader VirtueBench V2 evaluator. |
| `prudence/scenarios.csv` | ~0.4 MB | `8ac298fb67321a61b1e5c9ea0ed3d6470305d8c1672236c8392be2af9dc8d399` | VirtueBench V2 Prudence scenarios. Same structure. Not used in headline. |
| `temperance/scenarios.csv` | ~0.4 MB | `0a14831a165ce2190177f8899b6aaae5df66f260cb6bbf88ef8ee06f3af6327a` | VirtueBench V2 Temperance scenarios. Same structure. Not used in headline. |
| `steering/corpora.jsonl` | ~70 KB | `8217224cad34f6a637eda5f50274d62b4a6da534443147dd70c2b9b92b5dab97` | Steering reference corpora. Holds the `virtue=neutral, polarity=neutral` slice used as the **contrast pole** for `scripture_contrast` extraction (paper §3.3). These are short non-scriptural field-notes-style passages on astronomy, botany, navigation, etc. (170 records total across `christian`, `courage`, `justice`, `neutral`, `prudence`, `temperance`). |

## How to Verify

```bash
shasum -a 256 \
    data/bible_kjv.json \
    data/justice/scenarios.csv \
    data/courage/scenarios.csv \
    data/prudence/scenarios.csv \
    data/temperance/scenarios.csv \
    data/steering/corpora.jsonl
```

The output should match the table above. Hash mismatch means the data has
drifted from the canonical paper-run state; do not generate paper numbers
against drifted data without re-validating.

## Notes on Generation

`bible_kjv.json` was assembled from the public-domain King James Version by
`scripts/build_bible_json.py`. The KJV is in the public domain in the United
States and most jurisdictions.

`scenarios.csv` files are the VirtueBench V2 bank curated for the cardinal-virtue
papers in this org; the canonical record of how they were generated lives at
[christian-machine-intelligence/virtue-bench-2](https://github.com/christian-machine-intelligence/virtue-bench-2).

`steering/corpora.jsonl` was hand-curated for this project; entries are short
attestations of single-action prose under a tagged `virtue` and `polarity`.
The neutral slice (used as the scripture-contrast pole) was deliberately
chosen to be non-religious and to stay clear of explicit moral content; this
matters for §3.3, because the extracted scripture-vector direction is the
mean-difference between scripture activations and these neutral activations,
L2-normalised.

## Model Pin

The paper's headline numbers were produced on **Qwen/Qwen3-14B** in bf16. The
model revision is recorded in
[`src/virtue_bench/_model_pin.py`](../src/virtue_bench/_model_pin.py). Override
with the `--model-revision` flag on the CLI runners to test a different
snapshot.

> **The model pin is not yet verified.** Unlike the data hashes above, the pin
> currently records `revision="main"` rather than the exact commit SHA used for
> the May 2026 sweeps (`PINNING_STATUS: needs_verification`). `main` is a moving
> reference, so it does **not** guarantee you are loading the same weights the
> paper used. The SHA must be confirmed against the GPU host that ran the sweeps
> before this file can support an exact model-level reproduction. The data
> provenance below is unaffected by this.
