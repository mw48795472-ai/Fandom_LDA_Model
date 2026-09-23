# -*- coding: utf-8 -*-
"""L11 — 정규성 위반(Shapiro p<.01)·n=100 소표본에 대한 강건 회귀 병기.
보고서의 OLS 회귀 두 개(spillover ~ loyalty + activity, factor_diversity ~ loyalty + spillover)를 라이브·동결 각각에 대해
  OLS / Huber M-추정(statsmodels RLM, HuberT) / 중위수 분위회귀(QuantReg q=0.5) / 영향점 상위 5개(Cook's D) 제외 OLS
로 다시 적합해 계수 부호·유의성(p<0.05)이 같은지 표로 둔다. Pearson 옆의 Spearman은 이미 보고서에 있으므로 여기서는 회귀만 다룬다.
출력: Statistics/robust_regression_v7.json, Statistics/ROBUST_REGRESSION_V7.md
실행: python Statistics/robust_regression_v7.py
"""
import json
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

HERE = Path(__file__).resolve().parent; D = HERE.parent / "data" / "v7_final"
live = json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8")); frozen = json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))
MODELS = [("spillover ~ loyalty + activity", "spillover_score", ["loyalty_score", "activity"]), ("factor_diversity ~ loyalty + spillover", "factor_diversity", ["loyalty_score", "spillover_score"])]

def fits(y, X, names):
    Xc = sm.add_constant(X); out = {}
    ols = sm.OLS(y, Xc).fit(); out["OLS"] = ols
    out["Huber(RLM)"] = sm.RLM(y, Xc, M=sm.robust.norms.HuberT()).fit()
    out["Quantile(q=0.5)"] = sm.QuantReg(y, Xc).fit(q=0.5, max_iter=5000)
    cd = OLSInfluence(ols).cooks_distance[0]; keep = np.argsort(-cd)[5:]; keep = np.sort(keep)
    out["OLS w/o Cook's top5"] = sm.OLS(y[keep], Xc[keep]).fit(); dropped = [int(i) for i in np.argsort(-cd)[:5]]
    res = {}
    for k, f in out.items():
        res[k] = {"coef": {nm: round(float(f.params[i + 1]), 4) for i, nm in enumerate(names)}, "se": {nm: round(float(f.bse[i + 1]), 4) for i, nm in enumerate(names)},
                  "p": {nm: round(float(f.pvalues[i + 1]), 5) for i, nm in enumerate(names)}, "n": int(f.nobs)}
    res["dropped_top5_idx"] = dropped; return res

result = {}
for label, scores in (("live_10020", live), ("frozen_7350", frozen)):
    names_f = [r["fandom"] for r in scores]; cols = {c: np.array([r[c] for r in scores], float) for c in ("loyalty_score", "spillover_score", "activity", "factor_diversity")}
    result[label] = {}
    for mname, yk, xs in MODELS:
        r = fits(cols[yk], np.column_stack([cols[x] for x in xs]), xs); r["dropped_top5"] = [names_f[i] for i in r.pop("dropped_top5_idx")]
        agree = {}
        for x in xs:
            signs = {k: np.sign(v["coef"][x]) for k, v in r.items() if isinstance(v, dict) and "coef" in v}; sig = {k: v["p"][x] < 0.05 for k, v in r.items() if isinstance(v, dict) and "coef" in v}
            agree[x] = {"same_sign_all": len(set(signs.values())) == 1, "same_significance_all": len(set(sig.values())) == 1, "sign_OLS": int(signs["OLS"]), "significant": sig}
        r["agreement"] = agree; result[label][mname] = r
json.dump({"methods": ["OLS", "Huber(RLM)", "Quantile(q=0.5)", "OLS w/o Cook's top5"], "results": result}, open(HERE / "robust_regression_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

md = ["# 강건 회귀 병기 (L11) — OLS 결론이 추정 방법에 따라 달라지는가\n",
      "팬충성도(W=0.954, p=0.0015)·파급효과(W=0.861, p<.001)는 정규성을 위반하고 n=100이다. 보고서의 OLS 두 개를 Huber M-추정·중위수 분위회귀·영향점 5개 제외 OLS로 다시 적합해 계수 부호와 유의성(p<0.05)이 같은지 본다. `robust_regression_v7.py`가 만든다.\n", "## 0. 결론\n"]
for label in result:
    for mname, r in result[label].items():
        a = r["agreement"]; parts = []
        for x, v in a.items():
            parts.append(f"{x}: 부호 {'일치' if v['same_sign_all'] else '**불일치**'}·유의성 {'일치' if v['same_significance_all'] else '**불일치** (' + ', '.join(k for k, s in v['significant'].items() if s != v['significant']['OLS']) + ')'}")
        md.append(f"- {label} · {mname}: " + "; ".join(parts))
md.append("\n## 1. 계수 표 (계수, SE, p)\n")
for label in result:
    for mname, r in result[label].items():
        xs = [x for x in r["agreement"]]
        md.append(f"### {label} — {mname}\n"); md.append("| 방법 | n | " + " | ".join(f"{x} 계수 (SE, p)" for x in xs) + " |\n|---|---|" + "---|" * len(xs))
        for k in ("OLS", "Huber(RLM)", "Quantile(q=0.5)", "OLS w/o Cook's top5"):
            v = r[k]; md.append(f"| {k} | {v['n']} | " + " | ".join(f"{v['coef'][x]} ({v['se'][x]}, {v['p'][x]})" for x in xs) + " |")
        md.append(f"\n영향점 제외 5개: {', '.join(r['dropped_top5'])}\n")
md.append("## 2. 한계\n1. Huber·분위회귀의 p값은 점근 근사라 n=100에서 정확하지 않다. 부호·유의성의 '일치 여부'만 읽는다.\n2. 영향점 제외는 Cook's D 상위 5개의 기계적 제외이며, BTS·god·이효리처럼 실제로 극단인 팬덤을 빼는 것이 분석 목적에 맞는지는 별개 문제다.\n3. 종속변수가 0∼1 min-max 점수라 분위회귀가 더 자연스러운 선택일 수 있으나, 보고서 본문은 OLS를 유지하고 이 문서를 병기한다.\n")
md.append("## 3. 파일\n| 파일 | 내용 |\n|---|---|\n| `robust_regression_v7.json` | 라이브·동결 × 모형 2 × 방법 4의 계수·SE·p·일치 여부 |\n| `robust_regression_v7.py` | 이 문서를 만드는 스크립트 |\n")
(HERE / "ROBUST_REGRESSION_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
for label in result:
    for mname, r in result[label].items(): print(label, mname, {x: (v["same_sign_all"], v["same_significance_all"]) for x, v in r["agreement"].items()})
