#!/usr/bin/env python3
"""Analyze the v2 dose-response battery: working yardstick (ideal_v2),
dose-response over alpha, and courage-effect vs A-bias decomposition.

Per (vector, alpha) we report TWO orthogonal shifts (steer vs control):
  - courage_shift = mean over items of (margin_steer - margin_control), where
    margin is signed toward the COURAGEOUS answer -> the real effect of interest.
  - towardA_shift = same but signed toward the letter 'A' -> the position/letter bias.
A genuine courage direction: large courage_shift, small towardA_shift, monotone in
alpha, and reversed hurts. The `answer_bias` vector is the pure-A-bias reference
(large towardA, ~0 courage); `ideal_v2` is the positive-control yardstick.
"""
from __future__ import annotations
import argparse, json, math, statistics as st
from collections import defaultdict


def tcrit(df):  # ~0.975 two-sided
    if df >= 30: return 2.04
    return {1:12.7,2:4.30,3:3.18,4:2.78,5:2.57,6:2.45,8:2.31,10:2.23,15:2.13,20:2.09,25:2.06}.get(df, 2.2)


def stats(xs):
    n = len(xs)
    if n == 0: return dict(n=0, mean=float('nan'), ci=(float('nan'),)*2, p=float('nan'))
    m = st.mean(xs)
    if n == 1: return dict(n=1, mean=m, ci=(m, m), p=float('nan'))
    sd = st.stdev(xs); se = sd / math.sqrt(n)
    tc = tcrit(n - 1)
    t = m / se if se > 0 else float('inf')
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2)))) if se > 0 else 0.0
    return dict(n=n, mean=m, ci=(m - tc*se, m + tc*se), p=p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="results/courage_pilot/battery_v2_results.json")
    ap.add_argument("--output", default="results/courage_pilot/analyze_v2.json")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.input)); rows = d["results"]

    ctrl = {r["sample_id"]: r["margin"] for r in rows if r["condition"] == "control"}
    tgt = {r["sample_id"]: r["target"] for r in rows if r["condition"] == "control"}
    alphas = sorted({abs(r["alpha"]) for r in rows if r["condition"] != "control"})
    vectors = [v for v in ["ideal_v2", "answer_bias", "whole_bible", "courage_pool",
                           "ideal_courage", "random"] if any(r["vector"] == v for r in rows)]

    # validation gate
    gate = [(r["margin"] > 0) == (r["model_answer"] == r["target"])
            for r in rows if r["condition"] == "control" and r["margin"] != 0]
    gate_rate = sum(gate) / len(gate) if gate else float('nan')

    def shift(vec, cond, alpha, toward):  # toward in {"courage","A"}
        out = []
        for r in rows:
            if r["vector"] == vec and r["condition"] == cond and abs(r["alpha"]) == alpha and r["sample_id"] in ctrl:
                sid = r["sample_id"]
                def sgn(m):  # convert target-signed margin to toward-A if requested
                    return m if (toward == "courage" or tgt[sid] == "A") else -m
                out.append(sgn(r["margin"]) - sgn(ctrl[sid]))
        return out

    report = {"validation_gate": gate_rate, "alphas": alphas, "per_vector": {}}
    print("="*74)
    print("COURAGE STEERING v2 — dose-response + A-bias decomposition")
    print("="*74)
    print(f"validation gate (margin sign vs answer, control): {gate_rate*100:.0f}%  "
          f"({'PASS' if gate_rate>=0.8 else 'FAIL'})")
    print(f"alphas: {alphas}\n")
    print(f"{'vector':14} {'alpha':>5} {'courage_shift (95% CI)':>30} {'p':>9} {'towardA':>8} {'rev_courage':>12}")
    print("-"*84)
    for v in vectors:
        report["per_vector"][v] = {}
        for al in alphas:
            cs = stats(shift(v, "steer", al, "courage"))
            aA = stats(shift(v, "steer", al, "A"))
            rv = stats(shift(v, "reversed", al, "courage"))
            report["per_vector"][v][al] = dict(courage=cs, towardA=aA, reversed=rv)
            print(f"{v:14} {al:5.0f} {cs['mean']:+8.3f} [{cs['ci'][0]:+.2f},{cs['ci'][1]:+.2f}]  "
                  f"{cs['p']:9.5f} {aA['mean']:+8.3f} {rv['mean']:+12.3f}")
        print()

    # verdict
    def works(v, al):
        c = report["per_vector"].get(v, {}).get(al)
        return c and c["courage"]["mean"] > 0 and c["courage"]["ci"][0] > 0
    top = alphas[-1]
    yard_ok = any(works("ideal_v2", al) for al in alphas)
    def dose_monotone(v):
        ms = [report["per_vector"][v][al]["courage"]["mean"] for al in alphas]
        return all(ms[i] <= ms[i+1] for i in range(len(ms)-1)) and ms[-1] > 0
    print("="*74)
    print("VERDICT")
    print("="*74)
    print(f"  yardstick ideal_v2 steers courage: {'YES' if yard_ok else 'NO'}")
    for v in ["whole_bible", "courage_pool"]:
        if v not in report["per_vector"]: continue
        c = report["per_vector"][v][top]["courage"]; aA = report["per_vector"][v][top]["towardA"]
        rev = report["per_vector"][v][top]["reversed"]
        ab = report["per_vector"].get("answer_bias", {}).get(top, {}).get("courage", {}).get("mean", float('nan'))
        print(f"  {v} @a{top:.0f}: courage {c['mean']:+.2f} (CI {c['ci'][0]:+.2f}..{c['ci'][1]:+.2f}), "
              f"towardA {aA['mean']:+.2f}, reversed {rev['mean']:+.2f}, dose-monotone={dose_monotone(v)}")
    if not a.no_write:
        json.dump(report, open(a.output, "w"), indent=1)
        print(f"\nwrote {a.output}")


if __name__ == "__main__":
    main()
