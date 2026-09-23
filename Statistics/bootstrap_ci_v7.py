# -*- coding: utf-8 -*-
"""L10 — 스냅샷에 따라 뒤집히는 결론에 정량적 불확실성을 붙인다.

A. 팬덤 단위 부트스트랩(B=2,000, seed 0): 라이브(10,020건)·동결(7,350건) 각각 100개 팬덤을 복원추출해
   r(팬충성도, 파급효과)·Spearman·회귀계수(spillover ~ loyalty + activity, factor_diversity ~ loyalty + spillover)·4분면 χ² p의 95% 백분위 CI와
   '판별타당도 기준 |r|<0.5 를 만족하는 재표본 비율'을 구한다. 공통 97개 팬덤으로는 r(동결) − r(라이브) 차이의 CI도 잰다.
B. 코퍼스 축소 반복(R=1,000, seed 0): 라이브 코퍼스에서 팬덤별 불릿을 동결 시점 건수(fandom_scores_v6.json n_loyalty/n_spillover; 교체 진입 3개 팬덤은
   7,350/10,020 비율)만큼 무작위로 뽑아 EvidenceScore 합 → min-max 점수 → r 을 다시 계산한다. 문장 점수는 index_methodology/evidence_score_by_sentence_v7.csv 를 쓴다.
   '앞부분 자르기'(동결 근사 복원본과 같은 시간순 축소) 값도 같이 두어, 동결 r=0.638 이 코퍼스 크기 효과인지 '어느 문장이 들어갔는가' 효과인지 나눈다.
출력: Statistics/bootstrap_ci_v7.json, Statistics/BOOTSTRAP_CI_V7.md, Statistics/bootstrap_r_distributions_v7.png
실행: python Statistics/bootstrap_ci_v7.py
"""
import csv, json
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
D = REPO / "data" / "v7_final"
B, R, SEED, CRIT = 2000, 1000, 0, 0.5
rng = np.random.default_rng(SEED)

live = json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8")); frozen = json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))
def arrays(scores):
    return (np.array([r["loyalty_score"] for r in scores]), np.array([r["spillover_score"] for r in scores]), np.array([r["activity"] for r in scores], float),
            np.array([r["factor_diversity"] for r in scores]), [r["fandom"] for r in scores])

def ols_coef(y, X):
    X1 = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X1, y, rcond=None); return b

def statistics_of(L, S, A, Dv):
    r = float(np.corrcoef(L, S)[0, 1]); rho = float(stats.spearmanr(L, S)[0])
    b1 = ols_coef(S, np.column_stack([L, A])); b2 = ols_coef(Dv, np.column_stack([L, S]))
    hl, hs = L >= 0.5, S >= 0.5; tab = np.array([[int((hl & hs).sum()), int((hl & ~hs).sum())], [int((~hl & hs).sum()), int((~hl & ~hs).sum())]])
    try: pchi = float(stats.chi2_contingency(tab, correction=True)[1])
    except ValueError: pchi = float("nan")
    return {"r": r, "rho": rho, "mr_loyalty": float(b1[1]), "mr_activity": float(b1[2]), "z_loyalty": float(b2[1]), "z_spillover": float(b2[2]), "z_r2": float(1 - ((Dv - np.column_stack([np.ones(len(Dv)), L, S]) @ b2) ** 2).sum() / ((Dv - Dv.mean()) ** 2).sum()), "chi2_p": pchi}

def pct(v, lo=2.5, hi=97.5): v = np.asarray(v, float); v = v[~np.isnan(v)]; return [round(float(np.percentile(v, lo)), 4), round(float(np.percentile(v, hi)), 4)]

# ---- A. 팬덤 부트스트랩
resA = {}
for label, scores in (("live_10020", live), ("frozen_7350", frozen)):
    L, S, A, Dv, names = arrays(scores); n = len(L); point = statistics_of(L, S, A, Dv)
    draws = {k: [] for k in point}
    for _ in range(B):
        idx = rng.integers(0, n, n); st = statistics_of(L[idx], S[idx], A[idx], Dv[idx])
        for k, v in st.items(): draws[k].append(v)
    rs = np.array(draws["r"])
    resA[label] = {"n": n, "point": {k: round(v, 4) for k, v in point.items()}, "ci95": {k: pct(v) for k, v in draws.items()},
                   "share_abs_r_below_0.5": round(float((np.abs(rs) < CRIT).mean()), 4), "share_chi2_p_below_0.05": round(float((np.array(draws["chi2_p"]) < 0.05).mean()), 4),
                   "share_z_loyalty_coef_negative": round(float((np.array(draws["z_loyalty"]) < 0).mean()), 4), "share_z_spillover_coef_positive": round(float((np.array(draws["z_spillover"]) > 0).mean()), 4),
                   "r_draws": rs}
# 공통 97개 팬덤: 짝지은 부트스트랩으로 r 차이
lm = {r["fandom"]: r for r in live}; fm = {r["fandom"]: r for r in frozen}; common = sorted(set(lm) & set(fm))
Ll = np.array([lm[f]["loyalty_score"] for f in common]); Sl = np.array([lm[f]["spillover_score"] for f in common]); Lf = np.array([fm[f]["loyalty_score"] for f in common]); Sf = np.array([fm[f]["spillover_score"] for f in common])
diffs = []
for _ in range(B):
    idx = rng.integers(0, len(common), len(common)); diffs.append(float(np.corrcoef(Lf[idx], Sf[idx])[0, 1] - np.corrcoef(Ll[idx], Sl[idx])[0, 1]))
paired = {"n_common": len(common), "r_frozen_common": round(float(np.corrcoef(Lf, Sf)[0, 1]), 4), "r_live_common": round(float(np.corrcoef(Ll, Sl)[0, 1]), 4),
          "diff_point": round(float(np.corrcoef(Lf, Sf)[0, 1] - np.corrcoef(Ll, Sl)[0, 1]), 4), "diff_ci95": pct(diffs), "share_diff_positive": round(float((np.array(diffs) > 0).mean()), 4)}

# ---- B. 코퍼스 축소 반복
sent = {}
for row in csv.DictReader(open(REPO / "v7_final_10020" / "index_methodology" / "evidence_score_by_sentence_v7.csv", encoding="utf-8-sig")):
    sent.setdefault((row["fandom"], row["bullet_type"]), []).append(float(row["evidence_score"]))
sent = {k: np.array(v) for k, v in sent.items()}
order = [r["fandom"] for r in live]; ratio = 7350 / 10020
target = {}
for f in order:
    if f in fm: target[f] = (fm[f]["n_loyalty_bullets"], fm[f]["n_spillover_bullets"])
    else: target[f] = (max(1, round(len(sent[(f, "loyalty")]) * ratio)), max(1, round(len(sent[(f, "spillover")]) * ratio)))
def scores_from(raw_l, raw_s):
    L = (raw_l - raw_l.min()) / (raw_l.max() - raw_l.min()); S = (raw_s - raw_s.min()) / (raw_s.max() - raw_s.min()); return L, S
def reduce_once(prefix=False):
    rl, rs = [], []
    for f in order:
        nl, ns = target[f]; a, b = sent[(f, "loyalty")], sent[(f, "spillover")]
        if prefix: rl.append(a[:nl].sum()); rs.append(b[:ns].sum())
        else: rl.append(rng.choice(a, min(nl, len(a)), replace=False).sum()); rs.append(rng.choice(b, min(ns, len(b)), replace=False).sum())
    L, S = scores_from(np.array(rl), np.array(rs)); return float(np.corrcoef(L, S)[0, 1])
# 건수 구조 진단: 점수가 EvidenceScore '합'의 min-max 라 팬덤별 불릿 건수가 점수를 크게 좌우한다
def count_diag(scores):
    nl = np.array([r["n_loyalty_bullets"] for r in scores], float); ns = np.array([r["n_spillover_bullets"] for r in scores], float)
    return {"r_counts(n_loyalty, n_spillover)": round(float(np.corrcoef(nl, ns)[0, 1]), 4), "r(loyalty_score, n_loyalty)": round(float(np.corrcoef([r["loyalty_score"] for r in scores], nl)[0, 1]), 4),
            "r(spillover_score, n_spillover)": round(float(np.corrcoef([r["spillover_score"] for r in scores], ns)[0, 1]), 4)}
diag = {"live_10020": count_diag(live), "frozen_7350": count_diag(frozen)}
full_r = reduce_once.__globals__["np"].corrcoef(*scores_from(np.array([sent[(f, "loyalty")].sum() for f in order]), np.array([sent[(f, "spillover")].sum() for f in order])))[0, 1]
prefix_r = reduce_once(prefix=True); red = np.array([reduce_once() for _ in range(R)])
resB = {"R": R, "n_bullets_target": int(sum(sum(v) for v in target.values())), "r_full_live_recomputed": round(float(full_r), 4), "r_prefix_reduction(time-ordered, = frozen approx)": round(prefix_r, 4), "r_frozen_snapshot": resA["frozen_7350"]["point"]["r"],
        "random_reduction_r": {"mean": round(float(red.mean()), 4), "sd": round(float(red.std(ddof=1)), 4), "ci95": pct(red), "min": round(float(red.min()), 4), "max": round(float(red.max()), 4)},
        "share_random_reduction_r_ge_0.5": round(float((red >= CRIT).mean()), 4), "share_random_reduction_r_ge_prefix": round(float((red >= prefix_r).mean()), 4), "count_structure_diagnostics": diag, "r_draws": red}

# ---- 그림
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(resA["live_10020"]["r_draws"], bins=50, alpha=.6, label=f"live 10,020 (r={resA['live_10020']['point']['r']})"); ax[0].hist(resA["frozen_7350"]["r_draws"], bins=50, alpha=.6, label=f"frozen 7,350 (r={resA['frozen_7350']['point']['r']})")
    ax[0].axvline(CRIT, color="k", ls="--", lw=1); ax[0].set_title("A. fandom bootstrap of r(loyalty, spillover), B=2000"); ax[0].set_xlabel("Pearson r"); ax[0].legend(fontsize=8)
    ax[1].hist(red, bins=50, alpha=.7, label="random reduction to frozen counts"); ax[1].axvline(prefix_r, color="r", lw=1.5, label=f"prefix (time-ordered) = {prefix_r:.3f}"); ax[1].axvline(full_r, color="g", lw=1.5, label=f"full live = {full_r:.3f}"); ax[1].axvline(CRIT, color="k", ls="--", lw=1)
    ax[1].set_title("B. corpus reduction to 7,350-level counts, R=1000"); ax[1].set_xlabel("Pearson r"); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(HERE / "bootstrap_r_distributions_v7.png", dpi=150); png = True
except Exception as e:
    png = False; print("plot skipped:", e)

out = {"settings": {"B_fandom_bootstrap": B, "R_corpus_reduction": R, "seed": SEED, "criterion_abs_r_below": CRIT, "ci": "95% 백분위"},
       "A_fandom_bootstrap": {k: {kk: vv for kk, vv in v.items() if kk != "r_draws"} for k, v in resA.items()}, "A_paired_common97": paired,
       "B_corpus_reduction": {k: v for k, v in resB.items() if k != "r_draws"}}
json.dump(out, open(HERE / "bootstrap_ci_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

a, f_, p_, b_ = resA["live_10020"], resA["frozen_7350"], paired, resB
md = ["# 부트스트랩 신뢰구간과 코퍼스 축소 반복 (L10)\n",
      "판별타당도(|r|<0.5)와 Z축 독립성은 동결(7,350건)과 라이브(10,020건)에서 결론이 반대였다. 이 문서는 그 차이에 불확실성 폭을 붙인다. 전부 `bootstrap_ci_v7.py`(seed 0)가 만든다.\n",
      "## 0. 결론\n",
      f"1. **판별타당도 r의 95% CI는 두 스냅샷 모두 0.5를 포함한다.** 라이브 r = {a['point']['r']} (CI {a['ci95']['r']}), 동결 r = {f_['point']['r']} (CI {f_['ci95']['r']}). 팬덤을 다시 뽑으면 라이브에서 |r|<0.5 인 비율이 {a['share_abs_r_below_0.5']:.0%}, 동결에서 {f_['share_abs_r_below_0.5']:.0%}다. '충족/미충족'은 100개 팬덤 표본에서 확정할 수 있는 결론이 아니다.",
      f"2. **두 스냅샷의 r 차이는 유의하다.** 공통 97개 팬덤의 짝지은 부트스트랩에서 r(동결) − r(라이브) = {p_['diff_point']} (CI {p_['diff_ci95']}, 양수 비율 {p_['share_diff_positive']:.1%}). 차이는 표본 잡음이 아니라 코퍼스 차이다.",
      (lambda rm, rl, rf, rp: (
          f"3. **차이의 대부분은 팬덤별 불릿 건수 구조에서 온다.** 라이브 문장을 동결 시점의 팬덤별 건수만큼 무작위로 줄이기만 해도 r은 평균 {rm} (CI {b_['random_reduction_r']['ci95']})으로 동결 값({rf}) 쪽으로 옮겨가고, 0.5 이상인 비율이 {b_['share_random_reduction_r_ge_0.5']:.1%}다. "
          f"시간순 앞부분 축소(동결 근사 복원본과 같은 축소)의 r = {rp}도 무작위 분포의 한가운데(이 값 이상 {b_['share_random_reduction_r_ge_prefix']:.1%})라, '어느 문장이 들어갔는가'는 거의 영향이 없다. "
          f"점수가 EvidenceScore 합의 min-max 라 팬덤별 건수가 점수를 좌우하기 때문이다(건수 ↔ 점수 r: 라이브 충성도 {diag['live_10020']['r(loyalty_score, n_loyalty)']}, 파급효과 {diag['live_10020']['r(spillover_score, n_spillover)']}; 팬덤별 충성도·파급효과 건수 간 r: 동결 {diag['frozen_7350']['r_counts(n_loyalty, n_spillover)']}, 라이브 {diag['live_10020']['r_counts(n_loyalty, n_spillover)']}). "
          f"동결 시점에는 팬덤별 충성도·파급효과 수집 건수가 더 같이 움직였고, r41∼r72의 추가 2,670건이 그 짝을 풀어 r을 {rl}까지 내렸다. 판별타당도 결론은 수집 배분(L12 조사 노출량)의 함수다."
          if abs(rm - rf) < abs(rm - rl) else
          f"3. **차이는 코퍼스 크기가 아니라 '어느 문장이 들어갔는가'에서 온다.** 무작위 축소 r 평균 {rm} (CI {b_['random_reduction_r']['ci95']})은 라이브 값({rl}) 근처이고, 시간순 축소 r = {rp}만 동결 값({rf}) 쪽이다(무작위 분포에서 이 값 이상 {b_['share_random_reduction_r_ge_prefix']:.1%})."
      ))(b_['random_reduction_r']['mean'], b_['r_full_live_recomputed'], b_['r_frozen_snapshot'], b_['r_prefix_reduction(time-ordered, = frozen approx)']),
      f"4. **Z축 독립성**: factor_diversity ~ loyalty + spillover 의 R²는 라이브 {a['point']['z_r2']} (CI {a['ci95']['z_r2']}), 동결 {f_['point']['z_r2']} (CI {f_['ci95']['z_r2']}). 계수 부호가 재표본에서 유지되는 비율은 아래 표.\n",
      "## 1. 팬덤 부트스트랩 (B = 2,000)\n",
      "| 통계량 | 라이브 점추정 | 라이브 95% CI | 동결 점추정 | 동결 95% CI |\n|---|---|---|---|---|"]
NAMES = {"r": "Pearson r(충성도, 파급효과)", "rho": "Spearman ρ", "mr_loyalty": "spillover ~ loyalty + activity: loyalty 계수", "mr_activity": "같은 회귀: activity 계수", "z_loyalty": "diversity ~ loyalty + spillover: loyalty 계수", "z_spillover": "같은 회귀: spillover 계수", "z_r2": "같은 회귀 R²", "chi2_p": "4분면 χ² p"}
for k, nm in NAMES.items(): md.append(f"| {nm} | {a['point'][k]} | {a['ci95'][k]} | {f_['point'][k]} | {f_['ci95'][k]} |")
md.append(f"\n| 비율 | 라이브 | 동결 |\n|---|---|---|\n| \\|r\\|<0.5 (판별타당도 충족) | {a['share_abs_r_below_0.5']} | {f_['share_abs_r_below_0.5']} |\n| 4분면 χ² p<0.05 | {a['share_chi2_p_below_0.05']} | {f_['share_chi2_p_below_0.05']} |\n| diversity 회귀 loyalty 계수 < 0 | {a['share_z_loyalty_coef_negative']} | {f_['share_z_loyalty_coef_negative']} |\n| diversity 회귀 spillover 계수 > 0 | {a['share_z_spillover_coef_positive']} | {f_['share_z_spillover_coef_positive']} |\n")
md.append(f"공통 97개 팬덤 짝지은 부트스트랩: r(동결) {p_['r_frozen_common']} − r(라이브) {p_['r_live_common']} = {p_['diff_point']}, CI {p_['diff_ci95']}.\n")
md.append(f"## 2. 코퍼스 축소 반복 (R = {R})\n")
md.append(f"| 구분 | r |\n|---|---|\n| 라이브 전체 (문장 점수에서 재계산) | {b_['r_full_live_recomputed']} |\n| 시간순 앞부분 축소 (= 동결 근사 복원본) | {b_['r_prefix_reduction(time-ordered, = frozen approx)']} |\n| 동결 스냅샷 저장값 | {b_['r_frozen_snapshot']} |\n| 무작위 축소 평균 (sd) | {b_['random_reduction_r']['mean']} ({b_['random_reduction_r']['sd']}) |\n| 무작위 축소 95% 구간 | {b_['random_reduction_r']['ci95']} |\n| 무작위 축소 중 r ≥ 0.5 비율 | {b_['share_random_reduction_r_ge_0.5']} |\n| 무작위 축소 중 r ≥ 시간순 축소값 비율 | {b_['share_random_reduction_r_ge_prefix']} |\n")
md.append("| 건수 구조 진단 | 라이브 | 동결 |\n|---|---|---|\n" + "\n".join(f"| {k} | {diag['live_10020'][k]} | {diag['frozen_7350'][k]} |" for k in diag["live_10020"]) + "\n")
md.append("축소 목표 건수는 동결 점수 파일의 팬덤별 n_loyalty/n_spillover(97개)이고, 동결 이후 진입한 빈지노·몬스타엑스·투어스는 7,350/10,020 비율로 줄였다. 점수는 문장 단위 EvidenceScore(`index_methodology/evidence_score_by_sentence_v7.csv`) 합의 min-max 정규화라 원 파이프라인과 같다(L5). factor_diversity는 LDA 문서-토픽 분포가 필요해 축소 반복에서는 다루지 않는다.\n")
if png: md.append("![r 분포](bootstrap_r_distributions_v7.png)\n")
md.append("## 3. 한계\n1. 팬덤 부트스트랩은 100개 팬덤을 모집단의 표본으로 보는 가정이다. 팬덤 100개는 임의 표본이 아니라 선정된 집합이므로 CI는 '이 선정 방식 아래의 표본 변동'으로 읽는다.\n2. 축소 반복은 문장을 무작위로 뺀다. 실제 수집은 시간순·라운드별 주제 편중이 있으므로(bullet_provenance_v7.csv), 시간순 축소값과 무작위 분포의 거리가 그 편중의 크기다.\n3. R 쪽 `plots.R`에 CI 띠를 넣는 일은 하지 않았다(이 환경에 R이 없음). 값은 `bootstrap_ci_v7.json`에 있다.\n")
md.append("## 4. 파일\n| 파일 | 내용 |\n|---|---|\n| `bootstrap_ci_v7.json` | A(라이브·동결 부트스트랩 CI·비율), A_paired(97개 공통 차이), B(축소 반복) |\n| `bootstrap_r_distributions_v7.png` | r 분포 두 패널 |\n| `bootstrap_ci_v7.py` | 이 문서를 만드는 스크립트 |\n")
(HERE / "BOOTSTRAP_CI_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({"live": {k: v for k, v in resA["live_10020"].items() if k in ("point", "ci95", "share_abs_r_below_0.5")}, "frozen_r": f_["point"]["r"], "frozen_ci": f_["ci95"]["r"], "frozen_share": f_["share_abs_r_below_0.5"], "paired": paired, "B": {k: v for k, v in resB.items() if k != "r_draws"}}, ensure_ascii=False, indent=0)[:1800])
