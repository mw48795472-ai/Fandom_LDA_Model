# -*- coding: utf-8 -*-
"""
Statistics/R_통계검증/ (R) 이 대조하는 238개 항목을 파이썬(scipy·statsmodels)으로 같은 원본 JSON에서 재계산한다.
R이 설치되지 않은 환경에서 R 패키지의 "238/238 일치" 결과를 독립적으로 확인하기 위한 스크립트.

  2.1절 포지셔닝 맵 상관·회귀·영향점·χ²  (78)  정답지 data/v7_final/positioning_map_correlation_live_v7.json
  2.2절 3D Z축 독립성                     (80)  정답지 data/v7_final/chart3d_correlation_live_v7.json
  3.8절 K9/F6 검증                         (45)  정답지 data/v7_final/k9_validation_v7.json + 보고서 본문 상수
  7.4절 MCI 설명력                         (35)  정답지 보고서 7.4절 본문 표(상수) — 입력 Statistics/R_통계검증/data/member_mention_pilot_v7.json
                                                (= data/v7_final/member_mention_index_v7.json) + 동결 점수 fandom_scores_v6.json

비교 규칙은 R 쪽 ck_check()와 같다: 정답지에 기록된 유효 소수 자릿수까지 반올림 비교, p값은 허용오차(1e-12 / Spearman·Shapiro 1e-6).
실행: python Statistics/verify_r_sections_python.py   (scipy, statsmodels 필요)   종료 코드 0 = 전부 일치
"""
import json
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor

BASE = Path(__file__).resolve().parents[1]
D = BASE / "data" / "v7_final"
R_DATA = BASE / "Statistics" / "R_통계검증" / "data"

ok = tot = 0
bad = []


def ck(label, got, want, tol=None):
    global ok, tot
    if want is None:
        return
    tot += 1
    if isinstance(got, (int, float, np.floating, np.integer)) and isinstance(want, (int, float)) and not isinstance(want, bool):
        if tol is None:
            s = repr(float(want))
            dec = len(s.split(".")[1].rstrip("0")) if "." in s else 0
            good = round(float(got), dec) == round(float(want), dec)
        else:
            good = abs(float(got) - float(want)) <= tol
    else:
        good = got == want
    ok += bool(good)
    if not good:
        bad.append((label, got, want))


def fisher_ci(r, n):
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    return np.tanh([z - 1.959964 * se, z + 1.959964 * se])


def ols(y, X):
    Xc = sm.add_constant(X)
    return sm.OLS(y, Xc).fit(), Xc


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


live = load(D / "fandom_scores_live_reference_v7.json")
frozen = load(D / "fandom_scores_v6.json")
names = [r["fandom"] for r in live]
L = np.array([r["loyalty_score"] for r in live])
S = np.array([r["spillover_score"] for r in live])
A = np.array([r["activity"] for r in live])
Dv = np.array([r["factor_diversity"] for r in live])
n = len(L)


def section_2_1():
    t = load(D / "positioning_map_correlation_live_v7.json")
    r, p = stats.pearsonr(L, S)
    ck("n", n, t["n"]); ck("Pearson r", round(r, 4), t["pearson"]["r"]); ck("Pearson p", p, t["pearson"]["p_value"], 1e-12)
    ci = fisher_ci(r, n)
    ck("CI lo", round(ci[0], 4), t["pearson"]["ci95"][0]); ck("CI hi", round(ci[1], 4), t["pearson"]["ci95"][1]); ck("R²", round(r * r, 4), t["pearson"]["r_squared"])
    rho, sp = stats.spearmanr(L, S)
    ck("Spearman", round(rho, 4), t["spearman"]["rho"]); ck("Spearman p", sp, t["spearman"]["p_value"], 1e-6)
    for key, v in (("loyalty_score", L), ("spillover_score", S)):
        W, pw = stats.shapiro(v); tt = t["normality"][key]
        ck("SW W " + key, round(W, 4), tt["W"]); ck("SW p " + key, pw, tt["p_value"], 1e-6); ck("normal " + key, pw > 0.05, tt["normal_at_0.05"])
    for key, v in (("loyalty_score_vs_activity", L), ("spillover_score_vs_activity", S)):
        rr, pp = stats.pearsonr(v, A); tt = t["each_score_vs_activity"][key]
        ck("r " + key, round(rr, 4), tt["r"]); ck("p " + key, pp, tt["p_value"], 1e-12)
    f, Xc = ols(S, np.column_stack([L, A])); mr = t["multiple_regression_spillover_on_loyalty_activity"]
    ck("MR R²", round(f.rsquared, 4), mr["r_squared"]); ck("MR adj", round(f.rsquared_adj, 4), mr["adj_r_squared"])
    ck("MR F", round(f.fvalue, 3), mr["f_statistic"]); ck("MR F p", f.f_pvalue, mr["f_pvalue"], 1e-12)
    for i, nm in enumerate(["intercept", "loyalty_score", "activity"]):
        c = mr["coefficients"][nm]; dec = 6 if nm == "activity" else 4
        ck("coef " + nm, round(f.params[i], dec), c["coef"]); ck("se " + nm, round(f.bse[i], dec), c["se"])
        ck("t " + nm, round(f.tvalues[i], 3), c["t"]); ck("p " + nm, f.pvalues[i], c["p"], 1e-12)
    for i, nm in enumerate(["loyalty_score", "activity"]):
        ck("VIF " + nm, round(variance_inflation_factor(Xc, i + 1), 3), mr["vif"][nm])
    f1, _ = ols(S, L)
    ck("slope", round(f1.params[1], 4), t["regression_spillover_on_loyalty"]["slope"]); ck("intercept", round(f1.params[0], 4), t["regression_spillover_on_loyalty"]["intercept"])
    inf = OLSInfluence(f1); cd = inf.cooks_distance[0]; sr = inf.resid_studentized_internal; lev = inf.hat_matrix_diag
    ck("4/n", round(4 / n, 4), t["cooks_d_threshold_4_over_n"]); ck("n high", int((cd > 4 / n).sum()), t["n_high_influence_points"])
    for rk, idx in enumerate(np.argsort(-cd)[:5]):
        tt = t["influence_top5"][rk]
        ck(f"inf{rk+1} fandom", names[idx], tt["fandom"]); ck(f"inf{rk+1} std_resid", round(sr[idx], 3), tt["std_residual"])
        ck(f"inf{rk+1} cooks", round(cd[idx], 4), tt["cooks_d"]); ck(f"inf{rk+1} leverage", round(lev[idx], 4), tt["leverage"])
    for fnm, tt in t["sensitivity_remove_highlighted"].items():
        m = np.array([x != fnm for x in names]); rr, pp = stats.pearsonr(L[m], S[m])
        ck("sens r " + fnm, round(rr, 4), tt["r_without"]); ck("sens p " + fnm, pp, tt["p_without"], 1e-12)
    d = np.array([abs(np.corrcoef(np.delete(L, i), np.delete(S, i))[0, 1] - r) for i in range(n)]); loo = t["leave_one_out"]
    ck("LOO max", round(d.max(), 4), loo["max_abs_delta_r"]); ck("LOO fandom", names[int(d.argmax())], loo["max_delta_fandom"]); ck("LOO mean", round(d.mean(), 5), loo["mean_abs_delta_r"])
    hl, hs = L >= 0.5, S >= 0.5
    tab = np.array([[int((hl & hs).sum()), int((hl & ~hs).sum())], [int((~hl & hs).sum()), int((~hl & ~hs).sum())]])
    chi2, pc, dof, exp = stats.chi2_contingency(tab, correction=True); q = t["quadrant_chi_square"]
    for i in range(2):
        for j in range(2):
            ck(f"4분면[{i},{j}]", int(tab[i, j]), q["table"][i][j])
    ck("χ²", round(chi2, 4), q["chi2"]); ck("dof", dof, q["dof"]); ck("χ² p", pc, q["p_value"], 1e-12); ck("expected[0,0]", round(exp[0, 0], 2), q["expected"][0][0])
    ck("판별타당도", abs(r) < t["design_criterion"]["target_abs_r_below"], t["design_criterion"]["meets_criterion"])


def section_2_2():
    t = load(D / "chart3d_correlation_live_v7.json")
    ck("n", n, t["n"])
    for key, (a, b) in {"loyalty_vs_spillover": (L, S), "loyalty_vs_diversity": (L, Dv), "spillover_vs_diversity": (S, Dv)}.items():
        tt = t["pairwise"][key]; rr, pp = stats.pearsonr(a, b); ci = fisher_ci(rr, n); rho, sp = stats.spearmanr(a, b)
        ck("r " + key, round(rr, 4), tt["r"]); ck("p " + key, pp, tt["p_value"], 1e-12)
        ck("CI lo " + key, round(ci[0], 4), tt["ci95"][0]); ck("CI hi " + key, round(ci[1], 4), tt["ci95"][1])
        ck("R² " + key, round(rr * rr, 4), tt["r_squared"]); ck("ρ " + key, round(rho, 4), tt["spearman_rho"]); ck("ρ p " + key, sp, tt["spearman_p"], 1e-6)
    for key, v in (("loyalty_score", L), ("spillover_score", S), ("factor_diversity", Dv)):
        W, pw = stats.shapiro(v); tt = t["normality"][key]
        ck("SW W " + key, round(W, 4), tt["W"]); ck("SW p " + key, pw, tt["p_value"], 1e-6); ck("normal " + key, pw > 0.05, tt["normal_at_0.05"])
    f, Xc = ols(Dv, np.column_stack([L, S])); mr = t["multiple_regression_diversity_on_loyalty_spillover"]
    ck("MR R²", round(f.rsquared, 4), mr["r_squared"]); ck("MR adj", round(f.rsquared_adj, 4), mr["adj_r_squared"])
    ck("MR F", round(f.fvalue, 3), mr["f_statistic"]); ck("MR F p", f.f_pvalue, mr["f_pvalue"], 1e-12)
    for i, nm in enumerate(["intercept", "loyalty_score", "spillover_score"]):
        c = mr["coefficients"][nm]
        ck("coef " + nm, round(f.params[i], 4), c["coef"]); ck("se " + nm, round(f.bse[i], 4), c["se"])
        ck("t " + nm, round(f.tvalues[i], 3), c["t"]); ck("p " + nm, f.pvalues[i], c["p"], 1e-12)
    for i, nm in enumerate(["loyalty_score", "spillover_score"]):
        ck("VIF " + nm, round(variance_inflation_factor(Xc, i + 1), 3), mr["vif"][nm])
    inf = OLSInfluence(f); cd = inf.cooks_distance[0]; sr = inf.resid_studentized_internal; lev = inf.hat_matrix_diag
    ck("4/n", round(4 / n, 4), t["cooks_d_threshold_4_over_n"]); ck("n high", int((cd > 4 / n).sum()), t["n_high_influence_points"])
    for rk, idx in enumerate(np.argsort(-cd)[:5]):
        tt = t["influence_top5"][rk]
        ck(f"inf{rk+1} fandom", names[idx], tt["fandom"]); ck(f"inf{rk+1} std_resid", round(sr[idx], 3), tt["std_residual"])
        ck(f"inf{rk+1} cooks", round(cd[idx], 4), tt["cooks_d"]); ck(f"inf{rk+1} leverage", round(lev[idx], 4), tt["leverage"])
    for fnm, tt in t["sensitivity_remove_highlighted"].items():
        m = np.array([x != fnm for x in names]); fw, _ = ols(Dv[m], np.column_stack([L[m], S[m]]))
        ck("sens coef " + fnm, round(fw.params[1], 4), tt["loyalty_coef_without"]); ck("sens R² " + fnm, round(fw.rsquared, 4), tt["r_squared_without"])
    base = f.params[1]
    d = np.array([abs(ols(np.delete(Dv, i), np.column_stack([np.delete(L, i), np.delete(S, i)]))[0].params[1] - base) for i in range(n)])
    loo = t["leave_one_out_loyalty_coef"]
    ck("LOO max", round(d.max(), 4), loo["max_abs_delta_coef"]); ck("LOO fandom", names[int(d.argmax())], loo["max_delta_fandom"]); ck("LOO mean", round(d.mean(), 5), loo["mean_abs_delta_coef"])


def rank_first(vals, desc):
    order = sorted(range(len(vals)), key=lambda i: ((-vals[i]) if desc else vals[i], i))
    rk = [0] * len(vals)
    for pos, i in enumerate(order):
        rk[i] = pos + 1
    return rk


def section_3_8():
    k9 = load(D / "k9_validation_v7.json"); MEDIA = {"예능", "유튜브", "영화", "드라마", "방송", "출연"}
    ck("corpus_docs", k9["corpus_docs"], 9614); ck("vocab", k9["vocab_size"], 11924); ck("K=9 never tested", k9["existing_k_grid_never_tested_k9"], True)
    g = k9["k_grid"]; ks = [x["k"] for x in g]
    comp = [a + b + c + d for a, b, c, d in zip(rank_first([x["perplexity"] for x in g], False), rank_first([x["coherence"] for x in g], True),
                                                rank_first([x["diversity"] for x in g], True), rank_first([x["stability"] for x in g], True))]
    for i, k in enumerate(ks):
        ck(f"합성순위합 K={k}", comp[i], g[i]["composite_rank_sum"])
    ck("winner", ks[int(np.argmin(comp))], k9["k_grid_winner"]["k"]); ck("K=9 합", comp[ks.index(9)], 13); ck("K=8 합", comp[ks.index(8)], 9)
    ck("K=9 < K=8", comp[ks.index(9)] < comp[ks.index(8)], False)
    for tag, key, expected in (("K=9", "topics_k9", 2), ("K=8", "topics_k8", 3)):
        nw = 0
        for tp in k9[key]:
            hits = set(tp["top10"]) & MEDIA
            ck(f"{tag} T{tp['topic']} media hits", len(hits), tp["n_media_hits_top10"]); nw += len(hits) > 0
        ck(tag + " topics with media", nw, expected)
    ck("본문 '나머지 7개 토픽 0건' 일치", sum(1 for tp in k9["topics_k9"] if tp["n_media_hits_top10"] > 0) == 1, False)
    for tag, v in k9["subtag_doc_freq"].items():
        ck("subtag " + tag, round(v["doc_freq"] / k9["corpus_docs"] * 100, 2), v["pct_of_docs"])
    mg = k9["m_grid_on_k9_phi"]; sil = [m["silhouette"] for m in mg]; bi = int(np.argmax(sil)); iso = [bool(m.get("media_topic_isolated")) for m in mg]; fi = iso.index(True)
    ck("best M", mg[bi]["m"], 5); ck("best sil", sil[bi], 0.099); ck("iso M", mg[fi]["m"], 6); ck("iso sil", sil[fi], 0.081)
    ck("sil loss", round(sil[bi] - sil[fi], 3), 0.018); ck("iso at best", iso[bi], False)


def section_7_4():
    pv = load(R_DATA / "member_mention_pilot_v7.json"); fz = {r["fandom"]: r for r in frozen}; arch = load(D / "member_pilot_mci_correlation_v7.json")
    groups = sorted(set(pv) & set(fz)); ck("n groups", len(groups), 45); ck("names", groups, sorted(arch["groups"]))
    mci = np.array([pv[g]["mci_pilot"] for g in groups]); mc = np.array([len(pv[g]["member_mention_counts"]) for g in groups]); ex = mci - 1 / mc
    OUT = ["loyalty_score", "spillover_score", "coverage_index", "factor_diversity"]; Y = {o: np.array([fz[g][o] for g in groups]) for o in OUT}
    ck("MCI=Σshare² 불일치", sum(abs(round(sum(v ** 2 for v in pv[g]["member_impact_share_pilot"].values()), 3) - pv[g]["mci_pilot"]) > 0.0015 for g in groups), 0)
    ck("share 합=1 불일치", sum(abs(sum(pv[g]["member_impact_share_pilot"].values()) - 1) > 0.005 for g in groups), 0); ck("하한 위반", int((mci < 1 / mc - 1e-9).sum()), 0)
    ck("r MCI×멤버수", round(stats.pearsonr(mci, mc)[0], 3), -0.728)
    DOC = {"loyalty_score": (-0.385, 0.148, 0.009, -0.044, 0.002, 0.773), "spillover_score": (-0.066, 0.004, 0.665, 0.214, 0.046, 0.159),
           "coverage_index": (-0.056, 0.003, 0.715, 0.128, 0.016, 0.404), "factor_diversity": (-0.062, 0.004, 0.685, -0.157, 0.025, 0.304)}
    for o in OUT:
        for lab, pred, w in (("원시MCI", mci, DOC[o][:3]), ("MCI_excess", ex, DOC[o][3:])):
            rr, pp = stats.pearsonr(pred, Y[o])
            ck(f"{lab} r {o}", round(rr, 3), w[0]); ck(f"{lab} R² {o}", round(rr * rr, 3), w[1]); ck(f"{lab} p {o}", round(pp, 3), w[2])
    r2ex = {o: stats.pearsonr(ex, Y[o])[0] ** 2 for o in OUT}
    ck("excess best outcome", max(r2ex, key=r2ex.get), "spillover_score"); ck("excess best R²", round(max(r2ex.values()), 4), 0.0457)
    any_sig = False; max_vif = 0.0
    for o in OUT:
        f, Xc = ols(Y[o], np.column_stack([mci, mc])); any_sig |= bool(f.pvalues[1] < 0.05); max_vif = max(max_vif, variance_inflation_factor(Xc, 1))
    ck("MCI 편회귀 유의 존재", any_sig, False); ck("VIF<10", max_vif < 10, True); ck("4/n", round(4 / 45, 4), 0.0889)
    # 시점 기록: 아카이브 JSON(v7-55, 8,981건) vs 본 입력(최종 10,020건)
    print(f"  [시점] MCI×멤버수 r: 최종 입력 {stats.pearsonr(mci, mc)[0]:.4f} / 보고서 본문 -0.728 / v7-55 JSON {arch['mci_vs_member_count']['pearson_r']}")
    print(f"  [시점] 원시MCI×loyalty r: 최종 입력 {stats.pearsonr(mci, Y['loyalty_score'])[0]:.4f} / 본문 -0.385 / v7-55 JSON {arch['correlations_mci_raw']['loyalty_score']['pearson_r']}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    summary = []
    for title, fn in (("2.1절 포지셔닝 맵 상관계수", section_2_1), ("2.2절 3D Z축 독립성", section_2_2), ("3.8절 K9/F6 검증", section_3_8), ("7.4절 MCI 설명력", section_7_4)):
        o0, t0 = ok, tot
        fn()
        summary.append((title, ok - o0, tot - t0))
        print(f"{title}: {ok - o0}/{tot - t0} 일치")
    print(f"합계: {ok}/{tot} 일치")
    for b in bad:
        print("  불일치:", b)
    sys.exit(0 if not bad else 1)
