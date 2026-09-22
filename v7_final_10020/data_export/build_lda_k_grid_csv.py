# -*- coding: utf-8 -*-
"""
LDA 진단 JSON의 k_grid(K 후보별 perplexity/coherence/diversity/stability/composite_rank_sum)를
CSV로 풀고, selected_k와 일치하는 행에 selected=True 플래그를 붙인다.

기본값: 최종 라이브 참고 재적합(data/v7_final/lda_v6_diagnostics_live_reference_v7.json,
10,020건 코퍼스, selected_k=8) -> data/v7_final/lda_k_grid_live_reference_v7.csv
--src/--out 으로 동결 진단(lda_v6_diagnostics_frozen_v7_40.json)에도 사용 가능.
"""
import argparse
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(BASE / "data" / "v7_final" / "lda_v6_diagnostics_live_reference_v7.json"))
    ap.add_argument("--out", default=str(BASE / "data" / "v7_final" / "lda_k_grid_live_reference_v7.csv"))
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as f:
        diag = json.load(f)
    grid = diag["k_grid"]
    sel = diag["selected_k"]
    fields = ["k", "perplexity", "coherence", "diversity", "stability", "composite_rank_sum", "selected"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for g in grid:
            w.writerow({**{k: g[k] for k in fields[:-1]}, "selected": g["k"] == sel})
    best = min(grid, key=lambda g: g["composite_rank_sum"])
    print(f"rows={len(grid)} selected_k={sel} (composite_rank_sum 최솟값 행 k={best['k']}) "
          f"M={diag.get('selected_m_meta_factors')} silhouette={diag.get('meta_factor_silhouette')} -> {args.out}")
    assert best["k"] == sel, "selected_k must be the composite_rank_sum minimum"


if __name__ == "__main__":
    main()
